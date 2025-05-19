import pytest

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.expander.state import ExpanderState, StateLayer, ProcessingMode
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.tokenizer import Tokenizer
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token, TokenType
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
    expander.set_text(text)
    tokens = expander.process()

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


# def test_parse_brace_group():
#     text = r"""{OUTER{INNER}POST}"""

#     expander = ExpanderCore()
#     expander.set_text(text)
#     expander.parser.parse_element()  # parse beginning brace...
#     brace_group = expander.parse_brace_group()
#     assert brace_group == BraceNode(
#         [
#             TextNode("OUTER"),
#             BraceNode(
#                 [
#                     TextNode("INNER"),
#                 ]
#             ),
#             TextNode("POST"),
#         ]
#     )
