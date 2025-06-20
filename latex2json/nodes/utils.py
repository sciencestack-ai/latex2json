from typing import List, TypeVar, Callable
from latex2json.nodes.base_nodes import (
    TextNode,
    ASTNode,
)


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


T = TypeVar("T")


def split_nodes_by_predicate(
    nodes: List[T], predicate: Callable[[T], bool], keep_empty: bool = True
) -> List[List[T]]:
    """Split a list of nodes into sublists based on a predicate function.

    Args:
        nodes: List of nodes to split
        predicate: Function that returns True for separator nodes
        keep_empty: Whether to keep empty groups in the result

    Returns:
        List of node groups split by the predicate
    """
    groups: List[List[T]] = []
    current_group: List[T] = []

    for node in nodes:
        if predicate(node):
            if keep_empty or current_group:
                groups.append(current_group)
            current_group = []
        else:
            current_group.append(node)

    if keep_empty or current_group:
        groups.append(current_group)

    return groups
