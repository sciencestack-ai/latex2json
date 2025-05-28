from typing import List
from latex2json.nodes.base_nodes import (
    TextNode,
    ASTNode,
)


def convert_nodes_to_str(nodes: List[ASTNode]) -> str:
    return "".join(node.detokenize() for node in nodes)


def merge_text_nodes(nodes: List[ASTNode]) -> List[ASTNode]:
    """Merges consecutive TextNodes in a list."""
    merged = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if (
            isinstance(node, TextNode)
            and merged
            and isinstance(merged[-1], TextNode)
            and node.styles == merged[-1].styles
        ):
            merged[-1].text += node.text
        else:
            merged.append(node)
        i += 1
    return merged


def is_whitespace_node(node: ASTNode) -> bool:
    return isinstance(node, TextNode) and node.is_whitespace()


def strip_whitespace_nodes(nodes: List[ASTNode]):
    if nodes:
        while nodes and isinstance(nodes[0], TextNode):
            text = nodes[0].text.lstrip()
            if text:
                nodes[0].text = text
                break
            nodes.pop(0)

        while nodes and isinstance(nodes[-1], TextNode):
            text = nodes[-1].text.rstrip()
            if text:
                nodes[-1].text = text
                break
            nodes.pop(-1)
    return nodes
