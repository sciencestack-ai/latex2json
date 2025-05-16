from typing import List
from latex2json.nodes import (
    ASTNode,
    ArgNode,
    BraceNode,
    BracketNode,
    CommandNode,
    TextNode,
)

# from copy import deepcopy


def substitute_args(
    definition: List[ASTNode],
    args: List[ASTNode],
    depth: int = 1,
    math_mode: bool = False,
) -> List[ASTNode]:
    for i, node in enumerate(definition):
        if isinstance(node, ArgNode):
            if node.depth == depth:
                index = node.num - 1  # convert to 0-based index
                if index < len(args):
                    node.value = [args[index]]
        elif node.children:
            substitute_args(node.children, args, depth=depth, math_mode=math_mode)
    return extract_nodes(definition)


def extract_nodes(nodes: List[ASTNode]) -> List[ASTNode]:
    out = []
    for node in nodes:
        # if isinstance(node, BraceNode) or isinstance(node, BracketNode):
        #     out.extend(extract_nodes(node.children))
        if isinstance(node, ArgNode):
            out.extend(extract_nodes(node.value))
        elif isinstance(node, List):
            out.extend(extract_nodes(node))
        else:
            out.append(node)
    return out
