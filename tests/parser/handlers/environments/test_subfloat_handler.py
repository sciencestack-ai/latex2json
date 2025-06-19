import pytest
from latex2json.nodes import GroupNode, CaptionNode
from latex2json.nodes.base_nodes import TextNode
from latex2json.parser.parser import Parser


def test_subfloat_handler():
    parser = Parser()

    text = r"\subfloat [My Caption] {Body}"
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], GroupNode)
    assert out[0] == GroupNode(
        [CaptionNode([TextNode("My Caption")]), TextNode("Body")]
    )
