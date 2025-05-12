import pytest
from latex2json.nodes.csname_node import CSNameNode
from latex2json.nodes.syntactic_nodes import TextNode, CommandNode


def test_csname_node():
    # Test with text nodes
    nodes = [TextNode(" test"), TextNode("name ")]
    csname = CSNameNode(nodes)
    assert csname.get_literal() == "\\csname testname \\endcsname"
    assert csname.get_collapsed_literal() == "testname"

    # Test with command nodes
    nodes_with_cmd = [TextNode("test"), CommandNode("cmd")]
    csname_with_cmd = CSNameNode(nodes_with_cmd)
    # assert csname_with_cmd.get_literal() == "\\csnametestcmd\\endcsname"
    # assert csname_with_cmd.get_collapsed_literal() == "testcmd"

    # Test equality
    assert csname == CSNameNode([TextNode(" test"), TextNode("name ")])
    assert csname != CSNameNode([TextNode("different")])
