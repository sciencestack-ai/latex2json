from typing import List

from latex2json.nodes import ASTNode
from latex2json.parser.parser_core import Handler, ParserCore
from latex2json.parser.state import (
    FontSeries,
    FontShape,
    FontSize,
    FontFamily,
    FontStyle,
)
from latex2json.tokens.types import Token

LEGACY_TEXT_TO_STYLE = {
    "bf": FontSeries.BOLD,
    "it": FontShape.ITALIC,
}

TEXT_TO_STYLE = {
    "textbf": FontSeries.BOLD,
    "textit": FontShape.ITALIC,
}


def make_legacy_text_handler(style: FontStyle) -> Handler:
    def legacy_text_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
        parser.state.set_font(style)
        return []

    return legacy_text_handler


def make_text_handler(style: FontStyle) -> Handler:
    def text_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
        parser.skip_whitespace()
        nodes = parser.parse_brace_as_nodes()
        for node in nodes:
            node.add_styles([style.value])
        return nodes

    return text_handler


def register_text_handlers(parser: ParserCore):
    for cmd, style_str in LEGACY_TEXT_TO_STYLE.items():
        parser.register_handler(cmd, make_legacy_text_handler(style_str))

    for cmd, style_str in TEXT_TO_STYLE.items():
        parser.register_handler(cmd, make_text_handler(style_str))
