import pytest

from latex2json.nodes import TextNode
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.parser import Parser


def test_parse_immediate_node():
    """Test parse_immediate_token with braced groups and single tokens.

    parse_immediate_token parses either:
    - A braced group: {hello}
    - A single token: A
    """
    parser = Parser()

    # Test with braced group
    parser.set_text(r"{first}")
    out = parser.parse_immediate_node()
    out = strip_whitespace_nodes(out)
    assert len(out) == 1
    assert isinstance(out[0], TextNode)
    assert out[0].text == "first"

    # Test with single token where A is the first token
    parser.set_text(r"AB")
    out = parser.parse_immediate_node()
    out = strip_whitespace_nodes(out)
    assert len(out) == 1
    assert isinstance(out[0], TextNode)
    assert out[0].text == "A"
