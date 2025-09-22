import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import (
    assert_token_sequence,
    assert_tokens_startwith,
    assert_tokens_endwith,
)


def test_ifvoid_handler():
    expander = Expander()

    text = r"""
    \newbox\abstractbox
    \def\checkbox#1{
    \ifvoid#1
    TRUE
    \else
    FALSE
    \fi
    }
    \checkbox\abstractbox
"""
    out = expander.expand(text)

    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "TRUE"

    # now set content to the box
    text = r"""
    \setbox\abstractbox=\hbox{ABC}
    \checkbox\abstractbox
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "FALSE"

    # test with numeric id
    text = r"""
    \checkbox{0}
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "TRUE"

    # now setbox to 0
    text = r"""
    \setbox0=\hbox{ABC}
    \checkbox{0}
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "FALSE"
