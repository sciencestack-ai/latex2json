import pytest

from latex2json.nodes.semantic_nodes import SectionNode, ParagraphNode
from latex2json.nodes.syntactic_nodes import TextNode


def test_section_node():

    section = SectionNode(1, [TextNode("Hello")], [TextNode("World")])
    assert section.level == 1
    assert section.title == [TextNode("Hello")]
    assert section.content == [TextNode("World")]

    # check equality
    assert section == SectionNode(1, [TextNode("Hello")], [TextNode("World")])
    assert section != SectionNode(1, [TextNode("Hello")], [TextNode("Worlds")])


def test_paragraph_node():
    paragraph = ParagraphNode(1, "Hello", [TextNode("World")])
    assert paragraph.level == 1
    assert paragraph.title == "Hello"
    assert paragraph.content == [TextNode("World")]

    # check equality
    assert paragraph == ParagraphNode(1, "Hello", [TextNode("World")])
    assert paragraph != ParagraphNode(1, "Hello", [TextNode("Worlds")])
