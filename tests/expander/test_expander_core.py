import pytest

from latex2json.expander.expander import Expander
from latex2json.expander.expander_core import RELAX_TOKEN, ExpanderCore
from latex2json.expander.handlers.registers.base_register_handlers import (
    register_base_register_macros,
)
from latex2json.expander.handlers.registers.box_handlers import register_box_handlers
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.expander.state import ProcessingMode
from latex2json.registers import RegisterType
from latex2json.registers.utils import dimension_to_scaled_points
from latex2json.tokens.catcodes import Catcode, get_default_catcodes
from latex2json.tokens.tokenizer import Tokenizer
from latex2json.tokens.types import (
    BEGIN_BRACE_TOKEN,
    BEGIN_BRACKET_TOKEN,
    END_BRACE_TOKEN,
    END_BRACKET_TOKEN,
    EnvironmentEndToken,
    EnvironmentStartToken,
    EnvironmentType,
    Token,
    TokenType,
)
from latex2json.tokens.utils import wrap_tokens_in_braces
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

    expected = wrap_tokens_in_braces(TEST_CHARS)
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


def test_expand_text():
    expander = ExpanderCore()
    text = "1234"
    expander.set_text(text)
    assert expander.consume() == Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER)

    out = expander.expand_text("abc")
    assert out == expander.convert_str_to_tokens("abc")

    # ensure stream continues
    assert expander.consume() == Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER)
    assert expander.consume() == Token(TokenType.CHARACTER, "3", catcode=Catcode.OTHER)
    assert expander.consume() == Token(TokenType.CHARACTER, "4", catcode=Catcode.OTHER)
    assert expander.eof()


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
        ("$333$", [Token(TokenType.MATH_SHIFT_INLINE, "$")]),
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


def test_parse_keyword_and_sequences():
    expander = ExpanderCore()

    expander.set_text("plus")
    assert expander.parse_keyword("plus")
    assert not expander.parse_keyword("plus")
    assert expander.eof()

    expander.set_text("minus")
    assert not expander.parse_keyword("minux")
    assert expander.parse_keyword("minus")
    assert expander.eof()

    # test parse_keyword_sequence
    expander.makeatletter()
    expander.set_text(r"\@nil, \@nil\@@")
    assert expander.parse_keyword_sequence([r"\@nil", ",", r"\@nil", r"\@@"])
    assert expander.eof()

    # test wrong sequence
    expander.set_text(r"\@nil, \@nil\@@")
    assert not expander.parse_keyword_sequence([r"\@nil", "XXX", r"\@nil", r"\@@"])
    assert not expander.eof()
    # check that the stream is back to the original state
    assert expander.peek() == Token(TokenType.CONTROL_SEQUENCE, "@nil")
    assert expander.parse_keyword_sequence([r"\@nil", ",", r"\@nil", r"\@@"])
    assert expander.eof()

    expander.set_text("haha")
    assert expander.parse_keyword_sequence(["h", "a", "h", "a"])
    assert expander.eof()


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

    # test float with comma
    expander.set_text("-123,456")
    assert expander.parse_float() == -123.456

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

    # works with +/-
    expander.set_text(r"+22")
    assert expander.parse_integer() == 22

    expander.set_text(r"-22")
    assert expander.parse_integer() == -22

    expander.set_text(r"-22+44")
    assert expander.parse_integer() == -22
    assert expander.parse_integer() == 44

    # test only 1 decimal for floats
    expander.set_text(r"-1.2.3")
    assert expander.parse_float() == -1.2
    assert expander.parse_float() == 0.3
    assert expander.eof()

    # test hex + octal + ascii + sign
    expander.set_text(r"'101")
    assert expander.parse_integer() == 65
    assert expander.eof()

    expander.set_text(r'"41')
    assert expander.parse_integer() == 65
    assert expander.eof()

    expander.set_text(r'-"A')
    assert expander.parse_integer() == -10
    assert expander.eof()

    expander.set_text('"3C')
    assert expander.parse_integer() == 60
    assert expander.eof()

    expander.set_text('"C0FFEE')
    assert expander.parse_integer() == 12648430
    assert expander.eof()


def test_parse_dimensions():
    expander = ExpanderCore()
    register_base_register_macros(expander)

    expander.set_text("15pt")
    assert expander.parse_dimensions() == dimension_to_scaled_points(15, "pt")

    expander.set_text("2 in")
    assert expander.parse_dimensions() == dimension_to_scaled_points(2, "in")

    # parse with true keyword
    expander.set_text("10 true pt")
    assert expander.parse_dimensions() == dimension_to_scaled_points(10, "pt")
    assert expander.eof()

    # test with \relax
    expander.set_text(r"-2 \relax in")
    assert expander.parse_dimensions() == dimension_to_scaled_points(-2)

    expander.set_text(r"\relax")
    assert not expander.parse_dimensions()

    expander.set_text(r"0.2\relax33")
    assert expander.parse_dimensions() == dimension_to_scaled_points(0.2)

    expander.set_text(r"1234 i\relax n")
    assert expander.parse_dimensions() == dimension_to_scaled_points(1234, "i")

    # test parse dimensions with multiplier and register value
    dimen_100_value = 10
    expander.set_register(RegisterType.DIMEN, 100, dimen_100_value)
    expander.set_text(r"2\dimen100")  # should be 2x dimen_100_value
    assert expander.parse_dimensions() == 2 * dimen_100_value


def test_parse_skip():
    expander = Expander()

    expander.expand(r"\makeatletter")

    # base component only
    expander.set_text("10pt")
    out = expander.parse_skip()
    assert out == dimension_to_scaled_points(10, "pt")
    assert expander.eof()

    expander.set_text("10pt plus 2pt minus  5pt")
    out = expander.parse_skip()
    assert out == dimension_to_scaled_points(10 + 2 - 5, "pt")
    assert expander.eof()

    # test with \relax
    expander.set_text(r"10pt plus 2pt \relax minus 1pt")
    out = expander.parse_skip()
    assert out == dimension_to_scaled_points(10 + 2, "pt")
    assert not expander.eof()

    assert expander.parse_keyword(" minus 1pt")
    assert expander.eof()

    expander.set_text(r"5pt plus 2pt \@minus 1pt")
    out = expander.parse_skip()
    assert out == dimension_to_scaled_points(5 + 2 - 1, "pt")
    assert expander.eof()


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


def test_parse_box():
    expander = ExpanderCore()
    register_box_handlers(expander)

    expander.set_text(r"\hbox{Hello}")
    box = expander.parse_box()
    assert box is not None
    assert box.type == "hbox"
    assert box.content == expander.expand("Hello")
    assert expander.eof()

    expander.set_text(r"\vtop to 10pt{Hello2}")
    box = expander.parse_box()
    assert box is not None
    assert box.type == "vtop"
    assert box.content == expander.expand("Hello2")
    assert expander.eof()

    expander.set_text(r"\vbox  spread   10pt {Hello3}")
    box = expander.parse_box()
    assert box is not None
    assert box.type == "vbox"
    assert box.content == expander.expand("Hello3")
    assert expander.eof()


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


def test_math_shift_and_mode():
    expander = ExpanderCore()

    def check_math_catcodes():
        for char in ["_", "^", "&"]:
            assert expander.get_catcode(ord(char)) == Catcode.ACTIVE

    default_catcodes = get_default_catcodes()

    def check_text_catcodes():
        for char in ["_", "^", "&"]:
            assert expander.get_catcode(ord(char)) == default_catcodes[ord(char)]

    base_mode = expander.state.mode
    check_text_catcodes()

    expander.expand(r"$$")
    assert expander.state.is_math_mode
    assert expander.state.mode == ProcessingMode.MATH_DISPLAY
    check_math_catcodes()

    expander.expand(r"$$")
    assert not expander.state.is_math_mode
    assert expander.state.mode == base_mode

    check_text_catcodes()

    expander.expand(r"$")
    assert expander.state.is_math_mode
    assert expander.state.mode == ProcessingMode.MATH_INLINE

    check_math_catcodes()

    expander.expand(r"$")
    assert not expander.state.is_math_mode
    assert expander.state.mode == base_mode

    check_text_catcodes()

    # test one whole $...$
    out = expander.expand(r"$1^1$")
    assert_token_sequence(
        out,
        [
            Token(TokenType.MATH_SHIFT_INLINE, "$", 0),
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "^", catcode=Catcode.ACTIVE),
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.MATH_SHIFT_INLINE, "$"),
        ],
    )

    # check that mathmode is popped
    assert not expander.state.is_math_mode
    assert expander.state.mode == base_mode

    check_text_catcodes()

    # test one whole $$...$$
    out = expander.expand(r"$$1_1$$")
    assert_token_sequence(
        out,
        [
            Token(TokenType.MATH_SHIFT_DISPLAY, "$$", 0),
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "_", catcode=Catcode.ACTIVE),
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.MATH_SHIFT_DISPLAY, "$$"),
        ],
    )

    # check that mathmode is popped
    assert not expander.state.is_math_mode
    assert expander.state.mode == base_mode

    check_text_catcodes()


def test_consecutive_math_shifts():
    expander = ExpanderCore()

    out = expander.expand(r"$1$$$2$$")
    assert_token_sequence(
        out,
        [
            Token(TokenType.MATH_SHIFT_INLINE, "$"),
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.MATH_SHIFT_INLINE, "$"),
            Token(TokenType.MATH_SHIFT_DISPLAY, "$$"),
            Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
            Token(TokenType.MATH_SHIFT_DISPLAY, "$$"),
        ],
    )


# \( \), \[ \]
def test_math_macros():
    expander = Expander()

    out = expander.expand(r"\(1^1\)")
    assert_token_sequence(
        out,
        [
            Token(TokenType.MATH_SHIFT_INLINE, "$", 0),
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "^", catcode=Catcode.ACTIVE),
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.MATH_SHIFT_INLINE, "$"),
        ],
    )

    # \[ \] mock \begin{equation*} \end{equation*}

    out = expander.expand(r"\[1&1\]")
    assert_token_sequence(
        out,
        [
            EnvironmentStartToken("equation*", env_type=EnvironmentType.EQUATION),
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "&", catcode=Catcode.ACTIVE),
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            EnvironmentEndToken("equation*"),
        ],
    )

    # test weird edge case but valid latex
    out = expander.expand(r"\[1_1\$$$_$$2^2\]_^")
    expected = [
        EnvironmentStartToken("equation*", env_type=EnvironmentType.EQUATION),
        Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, "_", catcode=Catcode.ACTIVE),
        Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
        Token(TokenType.CONTROL_SEQUENCE, "$"),
        Token(TokenType.MATH_SHIFT_DISPLAY, "$$"),
        Token(TokenType.CHARACTER, "_", catcode=Catcode.SUBSCRIPT),
        Token(TokenType.MATH_SHIFT_DISPLAY, "$$"),
        Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, "^", catcode=Catcode.ACTIVE),
        Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
        EnvironmentEndToken("equation*"),
        Token(TokenType.CHARACTER, "_", catcode=Catcode.SUBSCRIPT),
        Token(TokenType.CHARACTER, "^", catcode=Catcode.SUPERSCRIPT),
    ]
    assert_token_sequence(out, expected)


def test_counter_macros():
    expander = ExpanderCore()
    assert expander.expand(r"\thesection") == expander.expand("0")
    expander.makeatletter()
    assert expander.expand(r"\c@section") == expander.expand("0")


def test_scope_and_catcodes():
    expander = ExpanderCore()

    assert expander.get_catcode(ord("@")) == Catcode.OTHER

    expander.push_scope()
    expander.makeatletter()
    assert expander.get_catcode(ord("@")) == Catcode.LETTER
    expander.pop_scope()
    assert expander.get_catcode(ord("@")) == Catcode.OTHER


def test_macro_scopes():
    expander = ExpanderCore()

    tokens_123 = expander.convert_str_to_tokens("123")
    tokens_abc = expander.convert_str_to_tokens("abc")

    expander.register_handler("test", lambda expander, token: tokens_123)
    assert expander.expand(r"\test") == tokens_123

    # now redefine \test in a new scope
    expander.push_scope()
    expander.register_handler("test", lambda expander, token: tokens_abc)
    assert expander.expand(r"\test") == tokens_abc

    # now pop the scope. Make sure it is still the old \test
    expander.pop_scope()
    assert expander.expand(r"\test") == tokens_123
