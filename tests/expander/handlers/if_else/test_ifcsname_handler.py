import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import (
    assert_token_sequence,
    assert_tokens_startwith,
    assert_tokens_endwith,
)


def test_ifcsname_handler():
    expander = Expander()

    text = r"""
\def\foo{foo}

\ifcsname foo\endcsname TRUE \else FALSE \fi % TRUE
\ifcsname xyzz\endcsname TRUE \else FALSE \fi % FALSE
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_str = out_str.replace("\n", "").replace(" ", "")
    assert out_str == "TRUEFALSE"
