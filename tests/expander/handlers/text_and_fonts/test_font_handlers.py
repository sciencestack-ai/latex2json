import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_font_n_newfont_handler():
    expander = Expander()

    # overrides \def\bigfont
    text = r"""
\def\bigfont{BIG FONT}
\font\bigfont=cmr10 at asdsd
\bigfont
"""
    out = expander.expand(text)

    # leave \bigfont as is
    assert expander.convert_tokens_to_str(out).strip() == r"\bigfont"

    assert expander.state.font_registry["bigfont"]

    text = r"""
    \newfont{\grecomath}{cmmi12 at 15pt}
    \grecomath
    """
    out = expander.expand(text)
    # leave \grecomath as is
    assert expander.convert_tokens_to_str(out).strip() == r"\grecomath"

    assert expander.state.font_registry["grecomath"]


def test_ignored_font_handlers():
    expander = Expander()

    text = r"""
    \makeatletter
\newfam\fontfam
\textfont\fontfam=\xxxx
\scriptfont\fontfam=\sss
\scriptscriptfont\fontfam=\yyy
\setmathfont[range=\setminus, Scale=MatchUppercase]{Asana-Math.otf}
\@setfontsize\normalsize\@xpt{13}
"""
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out == []
