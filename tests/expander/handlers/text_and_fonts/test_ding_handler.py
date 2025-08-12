import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_ding_handler():
    expander = Expander()

    # Test valid ding number
    text = r"\ding{172}"
    out = expander.expand(text)

    # Should return the mapped Unicode character
    expected_char = chr(9312)  # Unicode for ding 172
    assert expander.convert_tokens_to_str(out) == expected_char


def test_ding_handler_invalid_number():
    expander = Expander()

    # Test invalid ding number
    text = r"\ding{999}"
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)

    # Should return empty list for invalid number
    assert out == []


def test_ding_handler_non_numeric():
    expander = Expander()

    # Test non-numeric input
    text = r"\ding{abc}"
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)

    # Should return empty list for non-numeric input
    assert out == []
