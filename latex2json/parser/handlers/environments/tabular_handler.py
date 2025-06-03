from typing import Dict, List, Callable
from latex2json.nodes.tabular_node import CellNode, RowNode, TabularNode
from latex2json.nodes.utils import strip_whitespace_nodes, split_nodes_by_predicate
from latex2json.tokens import Catcode, EnvironmentStartToken, Token, TokenType
from latex2json.nodes import ASTNode, NewLineNode, AlignmentNode

from latex2json.parser.parser_core import ParserCore


def split_into_rows(nodes: List[ASTNode]) -> List[List[ASTNode]]:
    """Split nodes into rows based on NewLineNode"""
    return split_nodes_by_predicate(nodes, lambda n: isinstance(n, NewLineNode))


def split_nodes_into_columns(nodes: List[ASTNode]) -> List[CellNode]:
    """Split nodes into columns based on AlignmentNode and convert to CellNodes"""
    columns = split_nodes_by_predicate(nodes, lambda n: isinstance(n, AlignmentNode))
    return [merge_nodes_into_cellnode(col) for col in columns]


def merge_nodes_into_cellnode(
    nodes: List[ASTNode], strip_whitespace: bool = True
) -> CellNode:
    all_nodes: List[ASTNode] = []

    if strip_whitespace:
        nodes = strip_whitespace_nodes(nodes)

    max_rowspan = 1
    max_colspan = 1
    for node in nodes:
        if isinstance(node, CellNode):
            all_nodes.extend(node.body)
            max_rowspan = max(max_rowspan, node.rowspan)
            max_colspan = max(max_colspan, node.colspan)
        else:
            all_nodes.append(node)
    return CellNode(all_nodes, rowspan=max_rowspan, colspan=max_colspan)


def tabular_handler(parser: ParserCore, token: EnvironmentStartToken) -> List[ASTNode]:
    # parse as generic environment first
    out = parser.parse_environment(token)
    if not out:
        return []

    env_nodes: List[ASTNode] = out[0].body
    row_nodes: List[RowNode] = []
    if env_nodes:
        # Split into rows and columns using node-based splitting
        rows = split_into_rows(env_nodes)
        row_nodes = [RowNode(split_nodes_into_columns(row)) for row in rows]

        # strip null rows
        while row_nodes and row_nodes[0].is_null_row():
            row_nodes.pop(0)
        while row_nodes and row_nodes[-1].is_null_row():
            row_nodes.pop()

    return [TabularNode(row_nodes)]


TABULAR_ENV_NAMES = ["tabular", "longtable", "tabularx", "tabulary"]
TABULAR_ENV_NAMES.extend(name + "*" for name in TABULAR_ENV_NAMES[:])


def register_tabular_handlers(parser: ParserCore):
    for env_name in TABULAR_ENV_NAMES:
        parser.register_env_handler(env_name, tabular_handler)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
    \begin{tabular}{c}
        FIRST &
        \begin{tabular}{c}
            \begin{tabular}{c} 111 \end{tabular} \\ 22
        \end{tabular} \\
        44 & \begin{tabular}{c} 222 \end{tabular}
        & LAST
    \end{tabular}
    """.strip()
    # tokens = parser.expander.expand(text)
    out = parser.parse(text)
