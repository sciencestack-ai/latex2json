import pytest
from latex2json.nodes.base_nodes import TextNode
from latex2json.nodes.environment_nodes import SubTableNode, TableNode
from latex2json.parser.parser import Parser


def test_subfloat_handler():
    parser = Parser()

    text = r"""
    \begin{table}
    \subfloat [My Caption \label{subfig:1}] {Body}
    \end{table}
    """.strip()
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], TableNode)
    # check that inner subfloat defaults to subtablenode if parent is table

    body = out[0].body
    assert len(body) == 1
    assert isinstance(body[0], SubTableNode)

    subtable_node = body[0]
    assert subtable_node.labels == ["subfig:1"]

    caption_node = subtable_node.get_caption_node()
    assert caption_node and caption_node.numbering == "a"
    assert subtable_node.body == [
        caption_node,
        TextNode("Body"),
    ]
