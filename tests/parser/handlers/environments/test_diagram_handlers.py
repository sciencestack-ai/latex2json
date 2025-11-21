import pytest
from latex2json.nodes import DiagramNode
from latex2json.parser.parser import Parser


def test_xymatrix_with_spaces():
    """Test xymatrix command with whitespace"""
    parser = Parser()
    text = r"""
\xymatrix{ A & B \\ C & D }
""".strip()
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], DiagramNode)
    diagram_node = out[0]
    assert diagram_node.env_name == "xymatrix"
    assert diagram_node.diagram == text.strip()


def test_polylongdiv():
    """Test polylongdiv command with multiple braces"""
    parser = Parser()
    text = r"\polylongdiv{x^3 + 2x^2 + 3x + 4}{x + 1}"
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], DiagramNode)
    diagram_node = out[0]
    assert diagram_node.env_name == "polylongdiv"
    assert diagram_node.diagram == text.strip()
