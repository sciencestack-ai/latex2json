import pytest

from latex2json.expander.expander_core import RELAX_TOKEN, ExpanderCore
from latex2json.expander.handlers.registers.base_register_handlers import (
    register_base_register_macros,
)
from latex2json.registers import RegisterType
from latex2json.latex_maps.dimensions import dimension_to_scaled_points
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.tokenizer import Tokenizer
from latex2json.tokens.types import (
    BEGIN_BRACE_TOKEN,
    BEGIN_BRACKET_TOKEN,
    END_BRACE_TOKEN,
    END_BRACKET_TOKEN,
    Token,
    TokenType,
)
from tests.test_utils import assert_token_sequence

TEST_CHARS = [
    Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
    Token(TokenType.CHARACTER, "b", catcode=Catcode.LETTER),
    Token(TokenType.CHARACTER, "c", catcode=Catcode.LETTER),
    Token(TokenType.CHARACTER, "d", catcode=Catcode.LETTER),
]


def test_expander_core():
    expander = ExpanderCore()

    # standard process
    text = "{abcd}"
    tokens = expander.expand(text)

    expected = [
        BEGIN_BRACE_TOKEN,
        *TEST_CHARS,
        END_BRACE_TOKEN,
    ]
    assert_token_sequence(tokens, expected)

    # parse_brace_as_tokens
    expander.set_text(text)
    tokens = expander.parse_brace_as_tokens()
    assert_token_sequence(tokens, TEST_CHARS)


def test_expand_tokens():
    expander = ExpanderCore()

    text = "1234"
    expander.set_text(text)
    assert expander.peek() == Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER)

    # now expand arbitrary tokens in the middle
    x = expander.expand_tokens(TEST_CHARS)
    assert_token_sequence(x, TEST_CHARS)

    # check that the stream is back to the original state
    assert expander.peek() == Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER)


def test_whitespace_and_match():
    tokenizer = Tokenizer()
    expander = ExpanderCore(tokenizer)

    # test that all whitespace gets merged to single token
    text = r"""  Hi  % Hi surrounded by 2 whitespaces both sides"""
    expected_tokens = [
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "H", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, "i", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
    ]
    assert_token_sequence(expander.expand(text), expected_tokens)

    expander.set_text(r" \cmd @")
    assert expander.match(TokenType.CONTROL_SEQUENCE, value="cmd")
    expander.consume()
    assert expander.match(TokenType.CHARACTER, value="@")

    # now let's test setting the catcode of \ to WHITESPACE!
    expander.set_catcode(ord("\\"), Catcode.SPACE)
    expander.set_text(r"\cmd @")
    assert expander.peek() == Token(
        type=TokenType.CHARACTER, value="\\", catcode=Catcode.SPACE, position=0
    )
    # \ is now skipped with match!
    assert expander.match(TokenType.CHARACTER, value="c")
    expander.consume()
    assert expander.consume() == Token(
        TokenType.CHARACTER, value="m", catcode=Catcode.LETTER
    )
    assert expander.consume() == Token(
        TokenType.CHARACTER, value="d", catcode=Catcode.LETTER
    )
    # assert expander.match(TokenType.CHARACTER, value="@")  # , catcode=Catcode.OTHER)
    # assert expander.match(TokenType.CHARACTER, value="@", catcode=Catcode.OTHER)


def test_parse_immediate_token():
    expander = ExpanderCore()

    test_sequence_pairs = [
        (
            "{abc}2",
            [
                Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
                Token(TokenType.CHARACTER, "b", catcode=Catcode.LETTER),
                Token(TokenType.CHARACTER, "c", catcode=Catcode.LETTER),
            ],
        ),
        (r"\cmd sss", [Token(TokenType.CONTROL_SEQUENCE, "cmd")]),
        ("abc", [Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER)]),
        ("123", [Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER)]),
        ("$333$", [Token(TokenType.MATH_SHIFT, "$")]),
    ]

    for text, expected in test_sequence_pairs:
        expander.set_text(text)
        assert_token_sequence(expander.parse_immediate_token(), expected)

    # test character token sequence
    expander.set_text("abc")
    assert_token_sequence(
        expander.parse_immediate_token(),
        [Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER)],
    )
    assert_token_sequence(
        expander.parse_immediate_token(),
        [Token(TokenType.CHARACTER, "b", catcode=Catcode.LETTER)],
    )
    assert_token_sequence(
        expander.parse_immediate_token(),
        [Token(TokenType.CHARACTER, "c", catcode=Catcode.LETTER)],
    )
    assert expander.parse_immediate_token() is None


def test_parse_parameter_token():
    expander = ExpanderCore()

    expander.set_text("#1#22")
    assert expander.parse_parameter_token() == Token(TokenType.PARAMETER, "1")
    assert expander.parse_parameter_token() == Token(TokenType.PARAMETER, "2")
    assert expander.parse_parameter_token() is None
    assert expander.parse_integer() == 2
    assert expander.eof()

    expander.set_text("##1")
    assert expander.parse_parameter_token() == Token(
        TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER
    )
    assert expander.parse_integer() == 1
    assert expander.eof()

    # invalid single parameter token
    expander.set_text("#")
    assert expander.parse_parameter_token() is None
    assert expander.eof()

    expander.set_text("####4")
    assert expander.parse_parameter_token() == Token(
        TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER
    )
    assert expander.parse_parameter_token() == Token(
        TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER
    )
    assert expander.parse_integer() == 4
    assert expander.eof()


def test_parse_brace_as_tokens():
    expander = ExpanderCore()

    text = r"{Hi {abc} #12}"
    expander.set_text(text)
    tokens = expander.parse_brace_as_tokens()
    expected_tokens = [
        Token(TokenType.CHARACTER, "H", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, "i", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        BEGIN_BRACE_TOKEN,
        Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, "b", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, "c", catcode=Catcode.LETTER),
        END_BRACE_TOKEN,
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.PARAMETER, "1"),
        Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
    ]
    assert_token_sequence(tokens, expected_tokens)


def test_parse_bracket_as_tokens():
    expander = ExpanderCore()

    expander.set_text("[[abc] #1]")
    tokens = expander.parse_bracket_as_tokens()
    assert_token_sequence(
        tokens,
        [
            BEGIN_BRACKET_TOKEN,
            Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "b", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "c", catcode=Catcode.LETTER),
            END_BRACKET_TOKEN,
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.PARAMETER, "1"),
        ],
    )


# test helper functions
def test_parse_int_float_arguments():
    expander = ExpanderCore()

    expander.set_text("123 456")
    assert expander.parse_integer() == 123
    expander.skip_whitespace()
    assert expander.parse_integer() == 456

    expander.set_text("-10.234")
    assert expander.parse_integer() == -10

    expander.set_text(".333")
    assert expander.parse_integer() is None

    # test float
    expander.set_text("-123.456")
    assert expander.parse_float() == -123.456

    expander.set_text(".23fe")
    assert expander.parse_float() == 0.23

    # test with \relax\empty
    expander.set_text(r"0.23\relax44")
    assert expander.parse_float() == 0.23

    expander.set_text(r"0.23\empty44")
    assert expander.parse_float() == 0.2344

    # test with \relax\empty
    expander.set_text(r"123\relax4")
    assert expander.parse_integer() == 123

    expander.set_text(r"123\empty4")
    assert expander.parse_integer() == 1234

    expander.set_text(r"123\empty 4")
    assert expander.parse_integer() == 123

    expander.set_text(r"123\unknown4")
    assert expander.parse_integer() == 123
    assert expander.consume() == Token(TokenType.CONTROL_SEQUENCE, "unknown")
    assert expander.parse_integer() == 4
    assert expander.eof()

    # also works with \commands
    tokens_11 = expander.expand("11")
    expander.register_handler(r"\eleven", lambda x, y: tokens_11)
    expander.set_text(r"\eleven")
    assert expander.parse_integer() == 11

    tokens_12_relax = expander.expand(r"1\relax2")
    expander.register_handler(r"\twelverelax", lambda x, y: tokens_12_relax)
    expander.set_text(r"\twelverelax")
    assert expander.parse_integer() == 1  # relax token stops and is consumed
    assert expander.parse_integer() == 2

    tokens_13_empty = expander.expand(r"1\empty3")
    expander.register_handler(r"\thirteenempty", lambda x, y: tokens_13_empty)
    expander.set_text(r"-\thirteenempty")
    assert expander.parse_integer() == -13


def test_parse_dimensions():
    expander = ExpanderCore()

    expander.set_text("15pt")
    assert expander.parse_dimensions() == dimension_to_scaled_points(15, "pt")

    expander.set_text("2 in")
    assert expander.parse_dimensions() == dimension_to_scaled_points(2, "in")

    # test with \relax
    expander.set_text(r"-2 \relax in")
    assert expander.parse_dimensions() == dimension_to_scaled_points(-2)

    expander.set_text(r"\relax")
    assert not expander.parse_dimensions()

    expander.set_text(r"0.2\relax33")
    assert expander.parse_dimensions() == dimension_to_scaled_points(0.2)

    expander.set_text(r"1234 i\relax n")
    assert expander.parse_dimensions() == dimension_to_scaled_points(1234, "i")


def test_parse_register():
    expander = ExpanderCore()
    register_base_register_macros(expander)

    expander.set_text(r"\count100")
    assert expander.parse_register() == (RegisterType.COUNT, 100)

    # setting
    expander.expand(r"\count100=123")
    assert expander.get_register_value(RegisterType.COUNT, 100) == 123

    # test parse floats with registers
    expander.set_text(r"\count100")
    assert expander.parse_integer() == 123


def test_equality_ops():
    expander = ExpanderCore()

    expander.set_text(" =1")
    assert expander.parse_equals()
    assert expander.parse_integer() == 1
    expander.set_text(" s= ")
    assert not expander.parse_equals()

    # test changing catcode of = to LETTER
    expander.set_catcode(ord("="), Catcode.LETTER)
    expander.set_text("=")
    assert not expander.parse_equals()
    assert expander.consume() == Token(TokenType.CHARACTER, "=", catcode=Catcode.LETTER)

    # test angle brackets
    expander.set_text(" <")
    assert expander.parse_angle_brackets() == "<"

    expander.set_text(">")
    assert expander.parse_angle_brackets() == ">"

    expander.set_text(" s< ")
    assert not expander.parse_angle_brackets()

    expander.set_text(" s> ")
    assert not expander.parse_angle_brackets()

    # test changing catcode of < and > to LETTER
    expander.set_catcode(ord("<"), Catcode.LETTER)
    expander.set_catcode(ord(">"), Catcode.LETTER)
    expander.set_text("<")
    assert not expander.parse_angle_brackets()
    assert expander.consume() == Token(TokenType.CHARACTER, "<", catcode=Catcode.LETTER)

    expander.set_text(">")
    assert not expander.parse_angle_brackets()
    assert expander.consume() == Token(TokenType.CHARACTER, ">", catcode=Catcode.LETTER)


def test_parse_asterisk():
    expander = ExpanderCore()

    expander.set_text("*1")
    assert expander.parse_asterisk()
    assert expander.parse_integer() == 1


def test_empty_and_relax():
    expander = ExpanderCore()
    assert_token_sequence(expander.expand(r"\empty"), [])
    assert_token_sequence(expander.expand(r"\relax"), [RELAX_TOKEN])

    assert_token_sequence(expander.expand_tokens([RELAX_TOKEN]), [RELAX_TOKEN])
