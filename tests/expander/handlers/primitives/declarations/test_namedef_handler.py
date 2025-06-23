import pytest

from latex2json.expander.expander import Expander


def test_namedef_handler():
    expander = Expander()
    expander.expand(r"\makeatletter \@namedef{foo}#1:#2{bar #1:#2} \makeatother")
    out = expander.expand(r"\foo{a}:{b}")
    assert out == expander.expand("bar a:b")
    assert expander.check_macro_is_user_defined("foo")
