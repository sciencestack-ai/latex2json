from typing import List
from latex2json.latex_maps.environments import TABULAR_ENVIRONMENTS
from latex2json.nodes.base_nodes import CommandNode, TextNode
from latex2json.nodes.environment_nodes import EnvironmentNode
from latex2json.nodes.tabular_node import CellNode, RowNode, TabularNode
from latex2json.nodes.utils import (
    split_nodes_into_columns,
    split_text_on_braces,
    strip_whitespace_nodes,
)
from latex2json.parser.handlers.commands.command_handler_utils import (
    register_ignore_handlers_util,
)
from latex2json.parser.handlers.commands.tabular_cell_handlers import (
    merge_nodes_into_cellnode,
)
from latex2json.tokens import EnvironmentStartToken
from latex2json.nodes import ASTNode

from latex2json.parser.parser_core import ParserCore


def is_tabular_newline_command(node: ASTNode) -> bool:
    return isinstance(node, CommandNode) and node.name in ["\\", "tabularnewline"]


def split_nodes_into_columns_n_merge(nodes: List[ASTNode]) -> List[CellNode]:
    """Split nodes into columns based on AlignmentNode and convert to CellNodes"""
    columns = split_nodes_into_columns(nodes)
    return [merge_nodes_into_cellnode(col) for col in columns]


def split_nodes_into_rows_with_braces(nodes: List[ASTNode]) -> List[List[ASTNode]]:
    r"""Split nodes into rows based on \\\\ but only when not inside {} groups.

    Example:
        Input: [node1, {, node2, \\, node3, }, \\, node4]
        Output: [[node1, {, node2, \\, node3, }], [node4]]

        The \\ inside the {} group does not cause a split.
    """
    groups: List[List[ASTNode]] = []
    current_group: List[ASTNode] = []
    brace_depth = 0

    for node in nodes:
        if isinstance(node, TextNode):
            text = node.text
            if "{" in text or "}" in text:
                text_parts, brace_change = split_text_on_braces(text)
                for part in text_parts:
                    current_group.append(TextNode(part))
                brace_depth = max(0, brace_depth + brace_change)
                continue

        if brace_depth == 0 and is_tabular_newline_command(node):
            groups.append(current_group)
            current_group = []
        else:
            current_group.append(node)

    groups.append(current_group)
    return groups


def _convert_env_to_tabular_node(env_node: EnvironmentNode) -> TabularNode:
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
    return tabular_node


def tabular_handler(parser: ParserCore, token: EnvironmentStartToken) -> List[ASTNode]:
    # parse as generic environment first
    env_node = parser.parse_environment(token)
    if not env_node:
        return []

    tabular_node = _convert_env_to_tabular_node(env_node)
    return [tabular_node]


NICE_TABULAR_IGNORE_PATTERNS = ["CodeBefore", "CodeAfter", "Body", "rotate"]


def nice_tabular_handler(
    parser: ParserCore, token: EnvironmentStartToken
) -> List[ASTNode]:

    # strip out {...}[...] preamble
    parser.skip_whitespace()
    parser.parse_brace_as_nodes()
    parser.skip_whitespace()
    parser.parse_bracket_as_nodes()

    # parse as generic environment first
    env_node = parser.parse_environment(token)
    if not env_node:
        return []

    # strip out CodeBefore and Body and CodeAfter
    body = env_node.body
    filtered = []
    for node in body:
        # strip out CodeBefore and Body and CodeAfter
        if isinstance(node, CommandNode):
            if node.name in NICE_TABULAR_IGNORE_PATTERNS:
                continue
        filtered.append(node)
    env_node.set_body(filtered)
    tabular_node = _convert_env_to_tabular_node(env_node)
    return [tabular_node]


def register_tabular_handlers(parser: ParserCore):
    for env_name in TABULAR_ENVIRONMENTS:
        parser.register_env_handler(env_name, tabular_handler)
        parser.register_env_handler(env_name + "*", tabular_handler)

    for env_name in ["NiceTabular", "NiceTabular*", "NiceTabularX"]:
        parser.register_env_handler(env_name, nice_tabular_handler)

    # table stuff to ignore?
    ignored_env_pattern_N_blocks = {
        "columncolor": 1,  # Column colors
        "rowcolor": "[{",  # Row colors
        "rowcolors": 3,
        "bigstrut": "[",
        "arrayrulecolor": 1,
    }

    register_ignore_handlers_util(parser, ignored_env_pattern_N_blocks)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
    \definecolor{brickred}{HTML}{b92622}
\newcommand{\brickred}[1]{\textcolor{brickred}{#1}}

\begin{tabular}{rlll}
$\left( \mathbf{QK^\top} \odot \brickred{\mathcal{A}}\odot \mathbf{M}\right)\mathbf{V}$   
\end{tabular}
    """.strip()
    # tokens = parser.expander.expand(text)
    out = parser.parse(text, postprocess=True)
    out = strip_whitespace_nodes(out)
