import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_loop_handler():
    expander = Expander()

    text = r"""
\newcount\mycount
\mycount=1
\loop
  Item \the\mycount
  \advance\mycount by 1
\ifnum\mycount<3
\repeat
"""
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)

    out_str = expander.convert_tokens_to_str(out)
    assert (
        out_str == "Item 1Item 2"
    )  # this is now it looks like in latex. the whitespaces are stripped
