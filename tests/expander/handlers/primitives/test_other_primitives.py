import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import (
    EnvironmentEndToken,
    EnvironmentStartToken,
    Token,
    TokenType,
)
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.expander.handlers.sectioning.test_section_handlers import mock_section_token
from tests.test_utils import assert_token_sequence


def test_at_x_of_x_handler():
    expander = Expander()

    # if not defined, just define it
    text = r"""
\makeatletter
    
\@firstoftwo{ONE}{TWO}
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "ONE"

    assert expander.expand(r"\@secondoftwo{ONE}{TWO}") == expander.expand("TWO")


def test_dblarg_handler():
    expander = Expander()

    # if not defined, just define it
    text = r"""
\makeatletter
    
\def\foo@[#1]#2{Optional: #1; Mandatory: #2}
\def\foo{\@dblarg\foo@}
"""
    expander.expand(text)
    assert expander.get_macro("foo")
    assert expander.get_macro("foo@")

    out = expander.expand(r"\foo{long}")
    assert expander.convert_tokens_to_str(out) == "Optional: long; Mandatory: long"
    out = expander.expand(r"\foo[short]{long}")
    assert expander.convert_tokens_to_str(out) == "Optional: short; Mandatory: long"


def test_addpunct_handler():
    expander = Expander()

    text = r"""
\makeatletter
    
A\@addpunct{.}
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).replace(" ", "").replace("\n", "")
    assert out_str == "A."
