import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.catcodes import Catcode


def test_detokenize_with_percent():
    """Test that detokenize captures % characters in verbatim mode."""
    expander = Expander()

    # URL with percent-encoded characters
    text = r"\detokenize{a%20b%25c}"
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out)
    assert out_str == "a%20b%25c"
    assert "%" in out_str


def test_detokenize_complex_url():
    """Test detokenize with a realistic URL containing percent-encoded characters."""
    expander = Expander()

    # Complex URL from the detokenize.py example
    text = r"\detokenize{https://example.com?key=value%20with%20spaces&code=42%2B1}"
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out)
    # The URL should preserve the % characters
    assert "%" in out_str
    assert "value%20with%20spaces" in out_str
    assert "42%2B1" in out_str


def test_detokenize_preserves_special_chars():
    """Test that detokenize converts all non-space tokens to OTHER catcode."""
    expander = Expander()

    text = r"\detokenize{a_b^c}"
    out = expander.expand(text)

    # All characters should be converted to OTHER catcode (except spaces)
    for tok in out:
        if tok.value != " ":
            assert (
                tok.catcode == Catcode.OTHER
            ), f"Token '{tok.value}' should have catcode OTHER"
