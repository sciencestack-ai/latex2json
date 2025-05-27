from typing import List
from latex2json.nodes.syntactic_nodes import (
    BracketNode,
    TextNode,
    ASTNode,
)


def convert_bracket_node_to_literal_ast(bracket: BracketNode) -> List[ASTNode]:
    out = [TextNode("[")]
    for ele in bracket.children:
        if isinstance(ele, BracketNode):
            out.extend(convert_bracket_node_to_literal_ast(ele))
        else:
            out.append(ele)
    out.append(TextNode("]"))
    return out


def flatten(lst: List[List[ASTNode]]) -> List[ASTNode]:
    return [item for sublist in lst for item in sublist]


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
