from typing import Dict, List, Callable
from latex2json.latex_maps.environments import TABULAR_ENVIRONMENTS
from latex2json.nodes.tabular_node import CellNode, RowNode, TabularNode
from latex2json.nodes.utils import (
    split_nodes_by_predicate,
    split_nodes_into_rows,
)
from latex2json.parser.handlers.commands.tabular_cell_handlers import (
    merge_nodes_into_cellnode,
)
from latex2json.tokens import Catcode, EnvironmentStartToken, Token, TokenType
from latex2json.nodes import ASTNode, AlignmentNode

from latex2json.parser.parser_core import ParserCore


def split_nodes_into_columns(nodes: List[ASTNode]) -> List[CellNode]:
    """Split nodes into columns based on AlignmentNode and convert to CellNodes"""
    columns = split_nodes_by_predicate(nodes, lambda n: isinstance(n, AlignmentNode))
    return [merge_nodes_into_cellnode(col) for col in columns]


def tabular_handler(parser: ParserCore, token: EnvironmentStartToken) -> List[ASTNode]:
    # parse as generic environment first
    env_node = parser.parse_environment(token)
    if not env_node:
        return []

    env_nodes: List[ASTNode] = env_node.body
    row_nodes: List[RowNode] = []
    if env_nodes:
        # Split into rows and columns using node-based splitting
        rows = split_nodes_into_rows(env_nodes)
        row_nodes = [RowNode(split_nodes_into_columns(row)) for row in rows]

        # strip null rows
        while row_nodes and row_nodes[0].is_null_row():
            row_nodes.pop(0)
        while row_nodes and row_nodes[-1].is_null_row():
            row_nodes.pop()

    tabular_node = TabularNode(row_nodes)
    # re-assign labels from environment node
    tabular_node.labels = env_node.labels

    return [tabular_node]


def register_tabular_handlers(parser: ParserCore):
    for env_name in TABULAR_ENVIRONMENTS:
        parser.register_env_handler(env_name, tabular_handler)
        parser.register_env_handler(env_name + "*", tabular_handler)


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
