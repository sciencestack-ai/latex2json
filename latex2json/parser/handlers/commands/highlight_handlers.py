from typing import List

from latex2json.nodes import ASTNode
from latex2json.parser.parser_core import ParserCore
from latex2json.latex_maps.fonts import FontStyle, FontStyleType
from latex2json.tokens.types import Token


def sethlcolor_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
    r"""Handler for \sethlcolor{colorname} - sets highlight color state"""
    color_name = parser.parse_color_name()
    if not color_name:
        parser.logger.warning("\\sethlcolor expects a color name")
        return []

    parser.set_font(FontStyle(FontStyleType.HIGHLIGHT, color_name))
    return []


def hl_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
    r"""Handler for \hl{text} - highlights text with current highlight color"""
    parser.skip_whitespace()
    nodes = parser.parse_brace_as_nodes()
    if not nodes:
        return []

    # Get current highlight color from state, default to yellow
    highlight_color = parser.state.font_attributes.highlight_color or "yellow"

    for node in nodes:
        node.add_styles([f"highlight={highlight_color}"], insert_at_front=True)

    return nodes


def register_highlight_handlers(parser: ParserCore):
    r"""Register highlight-related command handlers"""
    parser.register_handler("sethlcolor", sethlcolor_handler, text_mode_only=True)
    parser.register_handler("hl", hl_handler, text_mode_only=True)
