from typing import List, Optional

from latex2json.nodes import ASTNode
from latex2json.nodes.base_nodes import TextNode
from latex2json.parser.parser_core import Handler, ParserCore
from latex2json.latex_maps.fonts import (
    FontStyle,
    LEGACY_TO_FONT_STYLE,
    LATEX_TO_FONT_STYLE,
    FontStyleType,
)
from latex2json.tokens.types import Token


def make_legacy_text_handler(style: FontStyle) -> Handler:
    def legacy_text_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
        parser.set_font(style)
        return []

    return legacy_text_handler


def make_text_handler(style: Optional[FontStyle] = None) -> Handler:
    def text_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
        parser.skip_whitespace()
        nodes = parser.parse_brace_as_nodes()
        if style:
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


def legacy_color_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
    parser.skip_whitespace()
    color_name_nodes = parser.parse_brace_as_nodes()
    if not color_name_nodes:
        parser.logger.warning("Warning: \\color expects a color name")
        return []

    color_name = "".join(
        [node.text for node in color_name_nodes if isinstance(node, TextNode)]
    )
    parser.set_font(FontStyle(FontStyleType.COLOR, color_name))
    return []


def reset_color_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
    parser.state.reset_font_color()
    return []


def frac_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
    blocks = parser.parse_braced_blocks(2)
    if len(blocks) != 2:
        parser.logger.warning("Warning: \\frac expects 2 arguments")
        return []
    return TextNode("(") + blocks[0] + TextNode(") / (") + blocks[1] + TextNode(")")


def citetext_handler(parser: ParserCore, token: Token) -> Optional[List[ASTNode]]:
    parser.skip_whitespace()
    return parser.parse_brace_as_nodes()


def register_text_handlers(parser: ParserCore):
    """
    Register text handling.
    Most of the handlers are only registered in text mode.
    Leave math-mode for katex
    """

    # Register legacy handlers
    for cmd, style_obj in LEGACY_TO_FONT_STYLE.items():
        parser.register_handler(
            cmd, make_legacy_text_handler(style_obj), text_mode_only=True
        )

    # Register handlers for commands that have FontStyle objects
    for cmd, style_obj in LATEX_TO_FONT_STYLE.items():
        parser.register_handler(cmd, make_text_handler(style_obj), text_mode_only=True)

    # Color handlers
    parser.register_handler("textcolor", textcolor_handler, text_mode_only=True)
    parser.register_handler("color", legacy_color_handler, text_mode_only=True)
    parser.register_handler("normalcolor", reset_color_handler, text_mode_only=True)

    # citetext
    parser.register_handler("citetext", citetext_handler)

    # other
    for backslash in ["backslash", "textbackslash", "arraybackslash"]:
        parser.register_handler(
            backslash, lambda parser, token: [TextNode(r"\\")], text_mode_only=True
        )

    parser.register_handler("indent", lambda parser, token: [TextNode("\t")])

    for frac in ["frac", "nicefrac", "textfrac"]:
        parser.register_handler(frac, frac_handler, text_mode_only=True)


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
