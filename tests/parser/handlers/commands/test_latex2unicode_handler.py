import pytest

from latex2json.nodes import CommandNode, TextNode, EquationNode
from latex2json.parser.parser import Parser


def test_basic_unicode_commands():
    parser = Parser()

    # test commands -> unicode
    text = r"\star \sqrt"
    out = parser.parse(text)
    assert out == [TextNode("⋆ √")]

    # test dont convert in mathmode
    text = r"$\sqrt3$"
    out = parser.parse(text)
    assert out == [EquationNode([CommandNode("sqrt"), TextNode("3")])]

    # # test unicode str
    # text = r"\u00a7"
    # out = parser.parse(text)
    # assert out == [TextNode("§")]

    # # test malformed unicode sequence
    # text = r"\u00a"
    # out = parser.parse(text)
    # assert out == [CommandNode("u"), TextNode("00a")]
