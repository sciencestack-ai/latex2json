import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_definecolor_handler():
    expander = Expander()

    # overrides \def\bigfont
    text = r"""
\definecolor{red}{rgb}{1,0,0}
"""
    out = expander.expand(text)

    out = strip_whitespace_tokens(out)
    # returns as \bigfont
    assert out == []

    assert expander.state.color_registry["red"]
