import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import (
    assert_tokens_endwith,
    assert_tokens_startwith,
    assert_token_sequence,
)


def test_ifstar_handler():
    expander = Expander()
    test_with_star = r"""
    \makeatletter
    \def\cmd{\@ifstar{star}{nostar}}
    \def\cmdpost{\@ifstar{star}{nostar}post} % the post after \@ifstar means \@ifstar false
    \makeatother
    """.strip()

    expander.expand(test_with_star)
    assert_token_sequence(expander.expand(r"\cmd*"), expander.expand("star"))
    assert_token_sequence(expander.expand(r"\cmdpost*"), expander.expand("nostarpost*"))


def test_nested_ifstar():
    expander = Expander()
    nested_test = r"""
    \makeatletter
    \def\outer{\@ifstar{\inner*}{\inner}}
    \def\inner{\@ifstar{star}{nostar}}
    \makeatother
    """.strip()

    expander.expand(nested_test)

    # Test outer star, inner star
    result = strip_whitespace_tokens(expander.expand(r"\outer*"))
    expected = strip_whitespace_tokens(expander.expand("star"))
    assert_token_sequence(result, expected)

    # Test outer no-star, inner star
    result = strip_whitespace_tokens(expander.expand(r"\outer"))
    expected = strip_whitespace_tokens(expander.expand("nostar"))
    assert_token_sequence(result, expected)


def test_ifstar_inside_iftrue():
    expander = Expander()
    test_code = r"""
    \makeatletter
    \def\cmd{\iftrue\@ifstar{star}{nostar}\fi}  % this is always nostar since \fi is right after \@ifstar block
    \makeatother
    """.strip()

    expander.expand(test_code)

    # Test with star
    result = strip_whitespace_tokens(expander.expand(r"\cmd*"))
    expected = strip_whitespace_tokens(expander.expand("nostar*"))
    assert_token_sequence(result, expected)


def test_ifnextchar_handler():
    expander = Expander()
    test_code = r"""
    \makeatletter
    \def\cmd{\@ifnextchar[{OPT}{NO OPT}} 
    \makeatother

    \cmd [ % OPT (DOES NOT CONSUME [)
    """.strip()
    out = expander.expand(test_code)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "OPT[", out_str


def test_undefined_handler():
    expander = Expander()
    text = r"""
    \makeatletter
    \@ifundefined{cmd}{undefined}{defined}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "undefined"

    text = r"""
    \@ifundefined\cmd{undefined}\relax
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "undefined"
