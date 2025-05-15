from typing import List

from latex2json.nodes import ASTNode, TextNode


def merge_text_nodes(nodes: List[ASTNode]) -> List[ASTNode]:
    """Merges consecutive TextNodes in a list."""
    merged = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if isinstance(node, TextNode) and merged and isinstance(merged[-1], TextNode):
            merged[-1].text += node.text
        else:
            merged.append(node)
        i += 1
    return merged
