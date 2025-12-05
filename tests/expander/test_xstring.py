"""Tests for xstring package handlers."""
import pytest
from latex2json.expander.expander import Expander


@pytest.fixture
def expander():
    """Create an expander instance for testing."""
    return Expander()


def test_ifbeginwith_match(expander):
    """Test \\IfBeginWith when string begins with prefix."""
    text = r"\IfBeginWith{foobar}{foo}{MATCH}{NO MATCH}"
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert result == "MATCH"


def test_ifbeginwith_no_match(expander):
    """Test \\IfBeginWith when string doesn't begin with prefix."""
    text = r"\IfBeginWith{foobar}{bar}{MATCH}{NO MATCH}"
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert result == "NO MATCH"


def test_ifbeginwith_multiword(expander):
    """Test \\IfBeginWith with multi-word strings."""
    text = r"\IfBeginWith{hello world}{hello}{YES}{NO}"
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert result == "YES"


def test_ifbeginwith_with_macros(expander):
    """Test \\IfBeginWith with macro expansion."""
    text = r"""
    \def\mystring{prefix_content}
    \IfBeginWith{\mystring}{prefix}{FOUND}{NOT FOUND}
    """
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert result == "FOUND"


def test_strgobble_left_basic(expander):
    """Test \\StrGobbleLeft with basic string."""
    text = r"\StrGobbleLeft{foobar}{3}"
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert result == "bar"


def test_strgobble_left_multiword(expander):
    """Test \\StrGobbleLeft with spaces."""
    text = r"\StrGobbleLeft{hello world}{6}"
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert result == "world"


def test_strgobble_left_too_many(expander):
    """Test \\StrGobbleLeft when count exceeds string length."""
    text = r"\StrGobbleLeft{test}{10}"
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert result == ""


def test_strgobble_left_zero(expander):
    """Test \\StrGobbleLeft with zero count."""
    text = r"\StrGobbleLeft{foobar}{0}"
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert result == "foobar"


def test_strgobble_right_basic(expander):
    """Test \\StrGobbleRight with basic string."""
    text = r"\StrGobbleRight{foobar}{3}"
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert result == "foo"


def test_strgobble_right_multiword(expander):
    """Test \\StrGobbleRight with spaces."""
    text = r"\StrGobbleRight{hello world}{6}"
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert result == "hello"


def test_strgobble_right_too_many(expander):
    """Test \\StrGobbleRight when count exceeds string length."""
    text = r"\StrGobbleRight{test}{10}"
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert result == ""


def test_strgobble_right_zero(expander):
    """Test \\StrGobbleRight with zero count."""
    text = r"\StrGobbleRight{foobar}{0}"
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert result == "foobar"


def test_combined_ifbeginwith_and_strgobble(expander):
    """Test combined usage of \\IfBeginWith and \\StrGobbleLeft."""
    text = r"""
    \def\mystring{prefix_content_suffix}
    \IfBeginWith{\mystring}{prefix}{
        \StrGobbleLeft{\mystring}{7}
    }{
        FAILED
    }
    """
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert result == "content_suffix"


def test_nested_string_operations(expander):
    """Test nested string manipulation operations."""
    text = r"""
    \def\original{abcdefgh}
    \StrGobbleRight{\StrGobbleLeft{\original}{2}}{2}
    """
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    # Should remove 'ab' from left (-> 'cdefgh'), then 'gh' from right (-> 'cdef')
    assert result == "cdef"
