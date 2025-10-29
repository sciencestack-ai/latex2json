import pytest

from latex2json.nodes import IncludeGraphicsNode, IncludePdfNode
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.parser import Parser


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


def test_ignore_graphicspath_handler():
    parser = Parser()
    text = r"\graphicspath{{example.pdf}}"
    out = parser.parse(text)
    assert len(out) == 0
