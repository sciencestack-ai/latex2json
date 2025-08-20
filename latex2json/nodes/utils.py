from typing import List, Type, TypeVar, Callable
from latex2json.nodes.base_nodes import (
    AlignmentNode,
    CommandNode,
    TextNode,
    ASTNode,
)
from latex2json.nodes.ref_cite_url_nodes import RefNode


def merge_text_nodes(nodes: List[ASTNode], ignore_styles=False) -> List[ASTNode]:
    """Merges consecutive TextNodes in a list."""
    merged = []
    i = 0
    while i < len(nodes):
        node = nodes[i]
        should_merge = False
        if isinstance(node, TextNode) and merged and isinstance(merged[-1], TextNode):
            should_merge = True
            if not ignore_styles and node.styles != merged[-1].styles:
                should_merge = False
        if should_merge:
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


def is_newline_command(node: ASTNode) -> bool:
    return isinstance(node, CommandNode) and node.name == "\\"


def split_nodes_into_rows(nodes: List[ASTNode]) -> List[List[ASTNode]]:
    """Split nodes into rows based on \\\\"""
    return split_nodes_by_predicate(nodes, is_newline_command)


def split_nodes_into_columns(nodes: List[ASTNode]) -> List[List[ASTNode]]:
    """Split nodes into columns based on AlignmentNode and convert to CellNodes"""
    return split_nodes_by_predicate(nodes, lambda n: isinstance(n, AlignmentNode))


# e.g. find_nodes_by_type(nodes, RefNode)
def find_nodes_by_type(nodes: List[ASTNode], node_type: Type[ASTNode]) -> List[ASTNode]:
    """Find all nodes of a specific type in a node tree.

    Args:
        nodes: List of nodes to search
        node_type: Type of node to find

    Returns:
        List of nodes matching the specified type
    """
    matching_nodes: List[ASTNode] = []
    for node in nodes:
        if isinstance(node, node_type):
            matching_nodes.append(node)
        elif node.children:
            matching_nodes.extend(find_nodes_by_type(node.children, node_type))
    return matching_nodes
