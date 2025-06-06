from typing import List

from latex2json.nodes import ASTNode
from latex2json.nodes.base_nodes import TextNode
from latex2json.parser.parser_core import Handler, ParserCore
from latex2json.latex_maps.fonts import (
    FontStyle,
    LEGACY_TO_FONT_STYLE,
    LATEX_TO_FONT_STYLE,
)
from latex2json.tokens.types import Token


def make_legacy_text_handler(style: FontStyle) -> Handler:
    def legacy_text_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
        parser.set_font(style)
        return []

    return legacy_text_handler


def make_text_handler(style: FontStyle) -> Handler:
    def text_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
        parser.skip_whitespace()
        nodes = parser.parse_brace_as_nodes()
        for node in nodes:
            # Use the frontend style mapping for consistent CSS-like values
            node.add_styles([style.value], insert_at_front=True)
        return nodes

    return text_handler


def textcolor_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
    parser.skip_whitespace()
    color_name_nodes = parser.parse_brace_as_nodes()
    if not color_name_nodes:
        parser.logger.warning("Warning: \\textcolor expects a color name")
        return []

    color_name = "".join(
        [node.text for node in color_name_nodes if isinstance(node, TextNode)]
    )

    nodes = parser.parse_brace_as_nodes()
    for node in nodes:
        node.add_styles(["color=" + color_name], insert_at_front=True)
    return nodes


def register_text_handlers(parser: ParserCore):
    # Register legacy handlers
    for cmd, style_obj in LEGACY_TO_FONT_STYLE.items():
        parser.register_handler(cmd, make_legacy_text_handler(style_obj))

    # Register handlers for commands that have FontStyle objects
    for cmd, style_obj in LATEX_TO_FONT_STYLE.items():
        parser.register_handler(cmd, make_text_handler(style_obj))

    # Special handlers
    parser.register_handler("textcolor", textcolor_handler)


if __name__ == "__main__":
    from latex2json.parser.parser import Parser

    parser = Parser()

    text = r"""
\definecolor{red}{rgb}{1,0,0}
\textcolor{red}{RED}
\textbf{Bold text}
\textit{Italic text}
\texttt{Monospace text}
\textsuperscript{superscript}
\underline{underlined text}
""".strip()

    out = parser.parse(text)
    # print(parser.state.get_styles_as_string())
