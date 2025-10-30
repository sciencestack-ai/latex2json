import pytest, os

from latex2json.expander.expander import Expander
from latex2json.tokens.types import TokenType
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import (
    assert_token_sequence,
    assert_tokens_startwith,
    assert_tokens_endwith,
)


dir_path = os.path.dirname(os.path.abspath(__file__))
test_data_path = os.path.join(dir_path, "../../../samples")


def test_requirepackage():
    expander = Expander()

    text = r"""
    \RequirePackage[opt]{%s/package1.sty}[2025/10/24]
    """ % (
        test_data_path
    )
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == ""

    assert expander.get_macro("foo")


def test_package_handlers():
    expander = Expander()

    # test replace package

    # package1.sty contains \newcommand{\foo}{bar}
    # package2.sty contains \newcommand{\bar}{foo}
    # so with \ReplacePackage, \bar should exist but not \foo
    text = r"""
    \ReplacePackage{%s/package1.sty}{%s/package2.sty}
""" % (
        test_data_path,
        test_data_path,
    )
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == ""

    assert expander.get_macro("bar")
    assert not expander.get_macro("foo")


def test_if_package_cls_handlers():
    expander = Expander()

    expander.makeatletter()
    text = r"""
    \@ifclasswith{article}{11pt}{
        TRUE
    }{
    FALSE
    }
    """
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "FALSE"
