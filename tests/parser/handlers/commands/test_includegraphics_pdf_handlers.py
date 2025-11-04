import pytest
import os

from latex2json.nodes import IncludeGraphicsNode, IncludePdfNode
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.parser import Parser

dir_path = os.path.dirname(os.path.abspath(__file__))
test_data_path = os.path.join(dir_path, "../../../samples")


def test_includegraphics_handler():
    parser = Parser()

    # no page
    text = r"\includegraphics{example.pdf}"
    out = parser.parse(text)
    out = strip_whitespace_nodes(out)
    assert len(out) == 1
    assert out[0] == IncludeGraphicsNode("example.pdf")

    # page
    text = r"\includegraphics[width=0.45\linewidth, page=3]{example.pdf}"

    out = parser.parse(text)
    out = strip_whitespace_nodes(out)
    assert len(out) == 1
    assert out[0] == IncludeGraphicsNode("example.pdf", page=3)


def test_includepdf_handler():
    parser = Parser()

    # no page
    text = r"\includepdf{example.pdf}"
    out = parser.parse(text)
    assert len(out) == 1
    assert out[0] == IncludePdfNode("example.pdf")

    # single page
    text = r"\includepdf[pages=1]{example.pdf}"
    out = parser.parse(text)
    assert len(out) == 1
    assert out[0] == IncludePdfNode("example.pdf", pages="1")

    # multi page
    text = r"\includepdf[pages={1-3,5}]{example.pdf}"
    out = parser.parse(text)
    assert len(out) == 1
    assert out[0] == IncludePdfNode("example.pdf", pages="1-3,5")

    # page range with 'last' keyword
    text = r"\includepdf[pages=1-last]{example.pdf}"
    out = parser.parse(text)
    assert len(out) == 1
    assert out[0] == IncludePdfNode("example.pdf", pages="1-last")

    # page range with 'last' keyword in braces
    text = r"\includepdf[pages={1-3,5-last}]{example.pdf}"
    out = parser.parse(text)
    assert len(out) == 1
    assert out[0] == IncludePdfNode("example.pdf", pages="1-3,5-last")


def test_ignore_graphicspath_handler():
    parser = Parser()
    text = r"\graphicspath{{example.pdf}}"
    out = parser.parse(text)
    assert len(out) == 0


def test_graphicspath_handler():
    parser = Parser()
    text = r"\graphicspath{{figures/}{images/}}"
    out = parser.parse(text)
    assert len(out) == 0
    assert "figures/" in parser.graphics_paths
    assert "images/" in parser.graphics_paths


def test_graphicspath_with_includegraphics():
    parser = Parser()

    # Parse the example.tex file which has graphicspath and includegraphics
    example_path = os.path.join(test_data_path, "example.tex")

    out = parser.parse_file(example_path)
    assert out and len(out) > 0
    out = strip_whitespace_nodes(out)

    # Find the IncludeGraphicsNode
    graphics_node = None
    for node in out:
        if isinstance(node, IncludeGraphicsNode):
            graphics_node = node
            break

    assert graphics_node is not None
    assert graphics_node.path == "images/image1.png"
