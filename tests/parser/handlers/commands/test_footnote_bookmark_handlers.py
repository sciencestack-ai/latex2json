import pytest

from latex2json.nodes.base_nodes import CommandNode, TextNode
from latex2json.nodes.ref_cite_url_nodes import FootnoteNode
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.parser import Parser


def test_ignore_bookmark_handlers():
    parser = Parser()

    text = r"""
    \pdfbookmark[1]{My bookmark}{my:bookmark}
    \belowpdfbookmark [1]{My bookmark}{my:bookmark}
    \currentpdfbookmark[1]{My bookmark}{my:bookmark}
    \bookmark[1] {My bookmark}
    \bookmark{My bookmark}
    """.strip()

    out = parser.parse(text)
    out = strip_whitespace_nodes(out)
    assert len(out) == 0


def test_footnote_handler():
    parser = Parser()
    text = r"\footnote{My footnote}"
    out = parser.parse(text)
    assert len(out) == 1
    assert out[0] == FootnoteNode("My footnote")

    # footnote with title
    text = r"\footnote[My title]{My footnote}"
    out = parser.parse(text)
    assert len(out) == 1
    assert out[0] == FootnoteNode("My footnote", "My title")

    # footnotemark
    text = r"\footnotemark"
    out = parser.parse(text)
    assert len(out) == 1
    assert out[0] == FootnoteNode("*")

    # footnotemark with title
    text = r"\footnotemark[My title]"
    out = parser.parse(text)
    assert len(out) == 1
    assert out[0] == FootnoteNode("My title")
