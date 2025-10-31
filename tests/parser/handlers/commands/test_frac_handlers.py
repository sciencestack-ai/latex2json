import pytest

from latex2json.nodes import TextNode
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.parser import Parser


def test_frac_handlers():
    parser = Parser()

    # Test with single tokens: \nicefrac 12 -> 1/2
    text = r"\nicefrac 12"
    out = parser.parse(text)
    out_str = parser.convert_nodes_to_str(out)
    assert out_str == "1/2"

    # Test with braced groups: \sfrac{AAA}{BBB} -> AAA/BBB
    text = r"\sfrac{AAA}{BBB}"
    out = parser.parse(text)
    out_str = parser.convert_nodes_to_str(out)
    assert out_str == "AAA/BBB"
