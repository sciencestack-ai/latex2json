import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_font_handler():
    expander = Expander()

    # overrides \def\bigfont
    text = r"""
\def\bigfont{BIG FONT}
\font\bigfont=cmr10 at asdsd
\bigfont
"""
    out = expander.expand(text)

    out = strip_whitespace_tokens(out)
    # returns as \bigfont
    assert_token_sequence(out, [Token(TokenType.CONTROL_SEQUENCE, "bigfont")])

    assert expander.state.font_registry["bigfont"]
