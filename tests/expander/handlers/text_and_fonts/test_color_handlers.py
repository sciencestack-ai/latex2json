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


def test_colorlet_alias():
    """Test \\colorlet as a simple alias of an existing color."""
    expander = Expander()

    text = r"""
\definecolor{myred}{rgb}{1,0,0}
\colorlet{danger}{myred}
"""
    expander.expand(text)

    assert expander.state.color_registry["danger"] == expander.state.color_registry["myred"]


def test_colorlet_unknown_base():
    """Test \\colorlet with a color name not in the registry (stores as-is)."""
    expander = Expander()

    text = r"\colorlet{colexam}{theme_blue}"
    expander.expand(text)

    assert expander.state.color_registry["colexam"] == "theme_blue"
