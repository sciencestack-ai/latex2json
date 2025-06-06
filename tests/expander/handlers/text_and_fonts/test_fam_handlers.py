import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_fam_handlers():
    expander = Expander()

    text = r"""
\newfam\fontfam
\textfont\fontfam=\xxxx
\scriptfont\fontfam=\sss
\scriptscriptfont\fontfam=\yyy
"""
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out == []
