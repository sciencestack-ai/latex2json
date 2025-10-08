from typing import List, Optional
from latex2json.expander.state import ProcessingMode
from latex2json.latex_maps.environments import MATH_ENVIRONMENTS
from latex2json.nodes import (
    EquationNode,
    EquationArrayNode,
    RowNode,
    CellNode,
)
from latex2json.nodes.base_nodes import DisplayType, TextNode
from latex2json.nodes.utils import (
    split_nodes_into_rows,
    strip_whitespace_nodes,
    split_nodes_into_columns,
)
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import EnvironmentStartToken, EnvironmentType, Token


def ensuremath_handler(parser: ParserCore, token: Token):
    is_math = parser.is_math_mode
    if not is_math:
        # push math mode inline
        parser.push_mode(ProcessingMode.MATH_INLINE)

    nodes = parser.parse_brace_as_nodes() or []
    if not is_math:
        # return as equation node itself
        parser.pop_mode()
        return [EquationNode(nodes)]

    # return as normal
    return nodes


def equation_align_handler(parser: ParserCore, token: EnvironmentStartToken):
    env = parser.parse_environment(token)

    env_def = parser.get_environment_definition(env.env_name)
    if not env_def or env_def.env_type != EnvironmentType.EQUATION_ALIGN:
        # if env is not equation_align, it means the env might have been redefined
        return [env]

    row_nodes: List[RowNode] = []
    row_numberings: List[Optional[str]] = []
    for node in env.children:
        if isinstance(node, EquationNode):
            column_nodes: List[CellNode] = []
            childs = node.children
            columns = split_nodes_into_columns(childs)
            for column in columns:
                column = strip_whitespace_nodes(column)
                column_nodes.append(CellNode(column))

            r_node = RowNode(column_nodes)
            r_node.labels = node.labels
            row_nodes.append(r_node)
            numbering = node.numbering
            if numbering:
                numbering = parser.sanitize_string(numbering)
            row_numberings.append(numbering)

    args_str = None
    if token.args:
        args_str = []
        for arg in token.args:
            args_str.append(parser.convert_tokens_to_str(arg))

    eq_array_node = EquationArrayNode(
        env.env_name,
        row_nodes=row_nodes,
        row_numberings=row_numberings,
        args_str=args_str,
    )
    eq_array_node.labels = env.labels
    return [eq_array_node]


def matrix_or_array_handler(parser: ParserCore, token: EnvironmentStartToken):
    env = parser.parse_environment(token)

    env_def = parser.get_environment_definition(env.env_name)
    if not env_def or env_def.env_type != EnvironmentType.EQUATION_MATRIX_OR_ARRAY:
        # if env is not matrix_or_array, it means the env might have been redefined
        return [env]

    childs = env.children
    rows = split_nodes_into_rows(childs)  # split \\
    row_nodes: List[RowNode] = []
    for r, row in enumerate(rows):
        # row = strip_whitespace_nodes(row)
        # if not row:
        #     continue
        columns = split_nodes_into_columns(row)  # split &
        column_nodes: List[CellNode] = []
        for c, column in enumerate(columns):
            column = strip_whitespace_nodes(column)
            column_nodes.append(CellNode(column))
        row_nodes.append(RowNode(column_nodes))

    args_str = None
    if token.args:
        args_str = []
        for arg in token.args:
            args_str.append(parser.convert_tokens_to_str(arg))

    eq_array_node = EquationArrayNode(
        env.env_name, row_nodes=row_nodes, args_str=args_str
    )
    eq_array_node.labels = env.labels
    return [eq_array_node]


def inline_math_handler(parser: ParserCore, token: EnvironmentStartToken):
    env = parser.parse_environment(token)
    return [EquationNode(env.children, equation_type=DisplayType.INLINE)]


def proof_cmd_handler(parser: ParserCore, token: Token):
    node = TextNode("Proof.")
    node.add_styles(["italic"])
    return [node]


def register_math_env_handlers(parser: ParserCore):
    parser.register_handler("ensuremath", ensuremath_handler)

    # lone \proof
    parser.register_handler("proof", proof_cmd_handler)

    for env_name, env_def in MATH_ENVIRONMENTS.items():
        # fetch env_def from parser/expander directly, in case it has been redefined
        if env_def.env_type == EnvironmentType.EQUATION_ALIGN:
            parser.register_env_handler(env_name, equation_align_handler)
            parser.register_env_handler(env_name + "*", equation_align_handler)

        elif env_def.env_type == EnvironmentType.EQUATION_MATRIX_OR_ARRAY:
            parser.register_env_handler(env_name, matrix_or_array_handler)
            parser.register_env_handler(env_name + "*", matrix_or_array_handler)

        elif env_name == "math":
            # inline!
            parser.register_env_handler("math", inline_math_handler)


if __name__ == "__main__":

    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
    \begin{align} 
    a & b \label{eq:1} \\
    \begin{matrix}  % number 8
    a & b \\
        c & d
    \end{matrix} 
    \\ 
    \begin{array}{2} % number 9
    a & b \\
        c & d
    \end{array} 44 \ref{eq:1} & 55 
    \end{align}

    \begin{equation}
    \begin{pmatrix}
    1 & 2 \ref{eq:1} & \text{mat}
    \end{pmatrix}
    \end{equation}
    """.strip()

    out = parser.parse(text, postprocess=True)
