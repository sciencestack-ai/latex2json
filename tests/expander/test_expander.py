import pytest

from latex2json.expander.expander import Expander
from latex2json.expander.macro_registry import Macro
from latex2json.expander.state import ExpanderState, StateLayer, ProcessingMode
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.tokenizer import Tokenizer


def test_bgroup_egroup():
    expander = Expander()

    # scoped
    expander.expand("\\bgroup")

    # test catcode change (local inside scope)
    assert expander.state.get_catcode(ord("@")) == Catcode.OTHER
    expander.set_catcode(ord("@"), Catcode.LETTER)
    assert expander.state.get_catcode(ord("@")) == Catcode.LETTER

    expander.expand("\\egroup")
    assert expander.state.get_catcode(ord("@")) == Catcode.OTHER


def test_catcode():
    expander = Expander()
    assert expander.state.get_catcode(ord("]")) == Catcode.OTHER
    expander.expand(r"\catcode`\]=3")
    assert expander.state.get_catcode(ord("]")) == 3


def test_makeatletter_makeatother():
    expander = Expander()

    assert expander.state.get_catcode(ord("@")) == Catcode.OTHER

    expander.expand("\\makeatletter")
    assert expander.state.get_catcode(ord("@")) == Catcode.LETTER

    expander.expand("\\makeatother")
    assert expander.state.get_catcode(ord("@")) == Catcode.OTHER


def test_def():
    expander = Expander()
    # expander.expand(r"\def\test{test}")
    # assert expander.macros.get("test") == "test"
