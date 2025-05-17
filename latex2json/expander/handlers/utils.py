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


if __name__ == "__main__":
    argnode1 = ArgNode(1, 1)
    argnode2 = ArgNode(2, 1)
    argnode_1_2 = ArgNode(1, 2)

    # e.g. #1 x #2 = ##1
    definition: List[ASTNode] = [
        argnode1,
        TextNode(" x "),
        argnode2,
        TextNode(" = "),
        argnode_1_2,
    ]

    depth1_args = [TextNode("100"), TextNode("2")]
    depth2_args = [TextNode("200")]
    substituted = substitute_args(definition, depth2_args, depth=argnode_1_2.depth)
    print(substituted)
