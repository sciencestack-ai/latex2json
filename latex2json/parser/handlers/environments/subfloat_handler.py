from typing import Optional
from latex2json.nodes.base_nodes import GroupNode
from latex2json.nodes.caption_node import CaptionNode
from latex2json.nodes.environment_nodes import (
    EnvironmentNode,
    SubFigureNode,
    SubTableNode,
)
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token


def subfloat_handler(parser: ParserCore, token: Token):
    if isinstance(parser.current_env, EnvironmentNode):
        env_name = parser.current_env.name
        # default to subfigure
        outer_node = SubTableNode([]) if env_name == "table" else SubFigureNode([])
    else:
        outer_node = GroupNode([])

    parser.push_env_stack(outer_node)

    parser.skip_whitespace()
    caption = parser.parse_bracket_as_nodes()
    parser.skip_whitespace()
    body = parser.parse_brace_as_nodes() or []
    body = strip_whitespace_nodes(body)

    parser.pop_env_stack(outer_node)

    caption_nodes = [CaptionNode(strip_whitespace_nodes(caption))] if caption else []
    body = caption_nodes + body
    outer_node.set_body(body)

    return [outer_node]


def register_subfloat_handler(parser: ParserCore):
    parser.register_handler("subfloat", subfloat_handler)


if __name__ == "__main__":
    from latex2json.parser.parser import Parser

    parser = Parser()
    text = r"""
    \begin{table}
    \subfloat [My Caption \label{subfig:1}] {Body}
    \caption{Table Caption}
    \label{tab:1}
    \end{table}
    """
    out = parser.parse(text)
    print(out)
