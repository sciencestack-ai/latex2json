import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_tokens_endwith, assert_tokens_startwith


def test_ifcase_handler():
    expander = Expander()

    text = r"""
    \ifcase 0
    Case 0
    \or
    Case 1
    \or
    Case 2
    \else 
    Default
    \fi"""
    out = expander.expand(text)
    assert expander.convert_tokens_to_str(out).strip() == "Case 0"

    # test with register
    text = r"""
    \newcount\mycount
    \mycount=1
    """
    expander.expand(text)

    text = r"""
    \ifcase \mycount
    Case 0
    \or
    Case 1
    \or
    Case 2
    \else 
    Default
    \fi"""
    out = expander.expand(text)
    assert expander.convert_tokens_to_str(out).strip() == "Case 1"

    expander.expand(r"\mycount=20")

    out = expander.expand(text)
    assert expander.convert_tokens_to_str(out).strip() == "Default"
