import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import (
    WHITESPACE_TOKEN,
    CommandWithArgsToken,
    Token,
    TokenType,
)
from latex2json.tokens.utils import strip_whitespace_tokens


def test_verb_handler():
    expander = Expander()

    text = r"""\verb|Hello| POST"""
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    expected = [
        CommandWithArgsToken("verb", args=[expander.convert_str_to_tokens("Hello")]),
        *expander.convert_str_to_tokens(" POST"),
    ]

    assert out == expected


def test_lst_inline_handler():
    expander = Expander()

    text = r"""\lstinline[language=python]|Hello| POST"""
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    expected = [
        CommandWithArgsToken(
            "lstinline",
            args=[expander.convert_str_to_tokens("Hello")],
            opt_args=[expander.convert_str_to_tokens("language=python")],
        ),
        *expander.convert_str_to_tokens(" POST"),
    ]
    assert out == expected

    # test with {...} as delimiter
    text = r"""\lstinline[language=python]{TRICKY} POST"""
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    expected = [
        CommandWithArgsToken(
            "lstinline",
            args=[expander.convert_str_to_tokens("TRICKY")],
            opt_args=[expander.convert_str_to_tokens("language=python")],
        ),
        *expander.convert_str_to_tokens(" POST"),
    ]
    assert out == expected
