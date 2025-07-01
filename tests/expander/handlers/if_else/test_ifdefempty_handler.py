import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_tokens_endwith, assert_tokens_startwith


def test_ifdefempty_handler():
    expander = Expander()
    text = r"""
    \ifdefempty{\a}{TRUE}{FALSE}
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert expander.convert_tokens_to_str(out) == "TRUE"

    text = r"""
    \def\a{AAA}
    \ifdefempty{\a}{TRUE}{FALSE}
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert expander.convert_tokens_to_str(out) == "FALSE"

    # now make \a empty
    text = r"""
    \def\a{}
    \ifdefempty{\a}{TRUE}{FALSE}
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert expander.convert_tokens_to_str(out) == "TRUE"
