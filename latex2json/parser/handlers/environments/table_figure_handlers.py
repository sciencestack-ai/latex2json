from typing import List
from latex2json.nodes.base_nodes import ASTNode
from latex2json.nodes.caption_node import CaptionNode
from latex2json.nodes.environment_nodes import (
    TableNode,
    FigureNode,
    SubTableNode,
    SubFigureNode,
)
from latex2json.parser.handlers.commands.command_handler_utils import (
    register_ignore_handlers_util,
)
from latex2json.parser.parser_core import ParserCore
from latex2json.registers.utils import int_to_alpha
from latex2json.tokens.types import EnvironmentStartToken, Token


def make_table_figure_handler(env_name: str = "table"):
    cls_node = TableNode if env_name == "table" else FigureNode

    def tabfig_handler(
        parser: ParserCore, token: EnvironmentStartToken
    ) -> List[ASTNode]:
        env = parser.parse_environment(token)
        out_node = cls_node(env.body, env.numbering)
        out_node.labels = env.labels

        # re-number all inner subfloat captions i.e. subtables/subfigures to be consistent
        counter = 0
        for child in out_node.body:
            if isinstance(child, (SubTableNode, SubFigureNode)):
                caption_node = child.get_caption_node()
                if caption_node:
                    counter += 1
                    roman_num = int_to_alpha(counter)
                    caption_node.numbering = roman_num

        return [out_node]

    return tabfig_handler


def subtable_handler(parser: ParserCore, token: EnvironmentStartToken) -> List[ASTNode]:
    env = parser.parse_environment(token)
    subtable_node = SubTableNode(env.body, env.numbering)
    subtable_node.labels = env.labels
    return [subtable_node]


def subfigure_env_handler(
    parser: ParserCore, token: EnvironmentStartToken
) -> List[ASTNode]:
    r"""\begin{subfigure}[]{}
    Not to be confused with \subfigure[]{}
    """
    env = parser.parse_environment(token)
    subfigure_node = SubFigureNode(env.body, env.numbering)
    subfigure_node.labels = env.labels
    return [subfigure_node]


def subfigure_cmd_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
    r"""\subfigure[caption]{...}
    Not to be confused with \begin{subfigure}
    """
    subfigure_node = SubFigureNode([])
    parser.push_env_stack(subfigure_node)
    parser.skip_whitespace()
    caption = parser.parse_bracket_as_nodes() or []
    parser.skip_whitespace()
    body = parser.parse_brace_as_nodes() or []
    body = [CaptionNode(caption)] + body
    subfigure_node.set_body(body)
    parser.pop_env_stack(subfigure_node)
    return [subfigure_node]


def register_table_figure_handlers(parser: ParserCore):
    # table
    for table_env_name in ["table", "table*"]:
        parser.register_env_handler(table_env_name, make_table_figure_handler("table"))
    # figure
    for figure_env_name in ["figure", "figure*"]:
        parser.register_env_handler(
            figure_env_name, make_table_figure_handler("figure")
        )

    # subtable
    parser.register_env_handler("subtable", subtable_handler)

    # subfigure env e.g. \begin{subfigure}
    parser.register_env_handler("subfigure", subfigure_env_handler)

    # subfigure cmd e.g. \subfigure[]{}
    parser.register_handler("subfigure", subfigure_cmd_handler)

    # ignore tablename and figurename
    ignore_patterns = {
        "tablename": 0,
        "figurename": 0,
    }
    register_ignore_handlers_util(parser, ignore_patterns)
