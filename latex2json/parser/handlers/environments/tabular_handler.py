from typing import Dict, List, Callable
from latex2json.latex_maps.environments import TABULAR_ENVIRONMENTS
from latex2json.nodes.base_nodes import CommandNode, SpecialCharNode, TextNode
from latex2json.nodes.tabular_node import CellNode, RowNode, TabularNode
from latex2json.nodes.utils import (
    is_newline_command,
    split_nodes_into_columns,
)
from latex2json.parser.handlers.commands.tabular_cell_handlers import (
    merge_nodes_into_cellnode,
)
from latex2json.tokens import Catcode, EnvironmentStartToken, Token, TokenType
from latex2json.nodes import ASTNode

from latex2json.parser.parser_core import ParserCore


def split_nodes_into_columns_n_merge(nodes: List[ASTNode]) -> List[CellNode]:
    """Split nodes into columns based on AlignmentNode and convert to CellNodes"""
    columns = split_nodes_into_columns(nodes)
    return [merge_nodes_into_cellnode(col) for col in columns]


def split_nodes_into_rows_with_braces(nodes: List[ASTNode]) -> List[List[ASTNode]]:
    r"""Split nodes into rows based on \\\\ but only when not inside special char braces {} groups.

    Example:
        Input: [node1, {, node2, \\, node3, }, \\, node4]
        Output: [[node1, {, node2, \\, node3, }], [node4]]

        The \\ inside the {} group does not cause a split.
    """
    groups: List[List[ASTNode]] = []
    current_group: List[ASTNode] = []
    brace_depth = 0

    for node in nodes:
        if isinstance(node, SpecialCharNode):
            if node.value == "{":
                brace_depth += 1
                continue
            elif node.value == "}":
                brace_depth = max(0, brace_depth - 1)  # Prevent negative depth
                continue

        if brace_depth == 0 and is_newline_command(node):
            groups.append(current_group)
            current_group = []
        else:
            current_group.append(node)

    groups.append(current_group)
    return groups


def tabular_handler(parser: ParserCore, token: EnvironmentStartToken) -> List[ASTNode]:
    # parse as generic environment first
    env_node = parser.parse_environment(token)
    if not env_node:
        return []

    env_nodes: List[ASTNode] = env_node.body
    row_nodes: List[RowNode] = []
    if env_nodes:
        # Split into rows and columns using node-based splitting
        rows = split_nodes_into_rows_with_braces(env_nodes)
        row_nodes = [RowNode(split_nodes_into_columns_n_merge(row)) for row in rows]

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
        \cline{1-1}\cline{3-3}
{\centering \textbf{Harmonic Loss}\\\citep{baek2025harmonic}\\Theorem \ref{thm:harmonic}}
    \end{tabular}
    """.strip()
    # tokens = parser.expander.expand(text)
    out = parser.parse(text, postprocess=True)
