import pytest
from latex2json.nodes.base_nodes import TextNode
from latex2json.parser.parser import Parser
from latex2json.nodes import EquationNode


def test_ensuremath_handler():
    parser = Parser()

    text = r"\ensuremath{x^2}"
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], EquationNode)
    assert out == [EquationNode([TextNode("x^2")])]
