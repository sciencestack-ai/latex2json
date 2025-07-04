from typing import List
from latex2json.nodes.base_nodes import ASTNode
from latex2json.nodes.environment_nodes import (
    TableNode,
    FigureNode,
    SubTableNode,
    SubFigureNode,
)
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import EnvironmentStartToken, Token


def table_handler(parser: ParserCore, token: EnvironmentStartToken) -> List[ASTNode]:
    env = parser.parse_environment(token)
    table_node = TableNode(env.body, env.numbering)
    table_node.labels = env.labels
    return [table_node]


def subtable_handler(parser: ParserCore, token: EnvironmentStartToken) -> List[ASTNode]:
    env = parser.parse_environment(token)
    subtable_node = SubTableNode(env.body, env.numbering)
    subtable_node.labels = env.labels
    return [subtable_node]


def figure_handler(parser: ParserCore, token: EnvironmentStartToken) -> List[ASTNode]:
    env = parser.parse_environment(token)
    figure_node = FigureNode(env.body, env.numbering)
    figure_node.labels = env.labels
    return [figure_node]


def subfigure_handler(
    parser: ParserCore, token: EnvironmentStartToken
) -> List[ASTNode]:
    env = parser.parse_environment(token)
    subfigure_node = SubFigureNode(env.body, env.numbering)
    subfigure_node.labels = env.labels
    return [subfigure_node]


def register_table_figure_handlers(parser: ParserCore):
    # table
    parser.register_env_handler("table", table_handler)
    parser.register_env_handler("table*", table_handler)
    # subtable
    parser.register_env_handler("subtable", subtable_handler)

    # figure
    parser.register_env_handler("figure", figure_handler)
    parser.register_env_handler("figure*", figure_handler)
    # subfigure
    parser.register_env_handler("subfigure", subfigure_handler)
