import pytest

from latex2json.expander.expander import Expander


def test_namedef_handler():
    expander = Expander()
    expander.expand(r"\makeatletter \@namedef{foo}{bar} \makeatother")
    out = expander.expand(r"\foo")
    assert out == expander.expand("bar")
