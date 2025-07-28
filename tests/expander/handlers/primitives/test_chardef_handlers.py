import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token, TokenType
from tests.test_utils import assert_token_sequence


def test_chardef_handlers():
    expander = Expander()

    text = r"""
    \chardef\test='101
    \test
    """
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "A"

    # mathchardef
    text = r"""
    \mathchardef\test 101
    \test
    """
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == str(chr(101))

    # chardefs are scoped
    text = r"""
    {
    \chardef\myA=65
    \myA
    }
    """
    out = expander.expand(text)
    assert not expander.get_macro("myA")
