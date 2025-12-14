import pytest
from latex2json.expander.expander import Expander


def test_url_with_percent():
    """Test that % characters in URLs are treated as verbatim, not comments"""
    expander = Expander()

    # Test URL with % characters - should be preserved, not treated as comments
    text = r"\url{https://www.google.com/%sdsd%33}"
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out)

    # The % should be preserved in the output
    assert out_str == r"\url{https://www.google.com/%sdsd%33}"
