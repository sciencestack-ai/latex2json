import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.catcodes import Catcode
from tests.test_utils import assert_token_sequence


def test_bgroup_egroup():
    expander = Expander()

    # scoped
    expander.expand("\\bgroup")

    # test catcode change (local inside scope)
    assert expander.get_catcode(ord("@")) == Catcode.OTHER
    expander.set_catcode(ord("@"), Catcode.LETTER)
    assert expander.get_catcode(ord("@")) == Catcode.LETTER

    expander.expand("\\egroup")
    assert expander.get_catcode(ord("@")) == Catcode.OTHER


def test_catcode():
    expander = Expander()
    assert expander.get_catcode(ord("]")) == Catcode.OTHER
    expander.expand(r"\catcode`\]=3")
    assert expander.get_catcode(ord("]")) == 3


def test_makeatletter_makeatother():
    expander = Expander()

    assert expander.get_catcode(ord("@")) == Catcode.OTHER

    expander.expand("\\makeatletter")
    assert expander.get_catcode(ord("@")) == Catcode.LETTER

    expander.expand("\\makeatother")
    assert expander.get_catcode(ord("@")) == Catcode.OTHER


def test_def():
    expander = Expander()
    expander.expand(r"\def\test{test}")
    assert expander.macros.get("test")
    assert_token_sequence(expander.expand(r"\test"), expander.expand("test"))


def test_redefine_primitives():
    expander = Expander()

    assert expander.get_macro("\\newcommand")
    assert expander.get_macro("\\def")

    # let's try to redefine \newcommand
    text = r"""
    \def\newcommand{NEWCOMMAND}
    """
    expander.expand(text)
    assert_token_sequence(
        expander.expand(r"\newcommand"), expander.expand("NEWCOMMAND")
    )


def test_empty():
    expander = Expander()
    assert_token_sequence(expander.expand(r"\empty"), [])
