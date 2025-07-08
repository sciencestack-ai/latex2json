import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_for_do_handler():
    expander = Expander()

    # first use \makeatletter for @
    expander.expand(r"\makeatletter")

    # test {...} case
    text = r"""
    \@for\item:={apple,banana,cherry}\do{%
        \item 
    }"""
    out = expander.expand(text)
    strip_whitespace_tokens(out)

    out_str = expander.convert_tokens_to_str(out)
    sequence = out_str.split("\n")
    sequence = [s.strip() for s in sequence if s.strip()]
    assert sequence == ["apple", "banana", "cherry"]

    # test without {}
    text = r"""
    \@for\@tempa:=-1,0,1,2,3,4,5\do{ 
     \@tempa
    }
"""
    out = expander.expand(text)
    strip_whitespace_tokens(out)

    out_str = expander.convert_tokens_to_str(out)
    sequence = out_str.split("\n")
    sequence = [s.strip() for s in sequence if s.strip()]
    assert sequence == ["-1", "0", "1", "2", "3", "4", "5"]
