import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_tokens_endwith, assert_tokens_startwith


def test_if_true_false_handler():
    expander = Expander()
    text = r"""
    \iftrue
        TRUE
    \else
        FALSE
    \fi""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert Expander.check_tokens_equal(out, expander.expand("TRUE"))


def test_nested_if_true_false_handler():
    expander = Expander()
    text = r"""
    \iftrue
        TRUE
        \iffalse
            INNER TRUE
        \else
            INNER FALSE
        \fi
    \else
        FALSE
    \fi
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert_tokens_startwith(out, expander.expand("TRUE"))
    assert_tokens_endwith(out, expander.expand("INNER FALSE"))
