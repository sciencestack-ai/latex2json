from typing import List, Optional

from latex2json.expander.state import ProcessingMode
from latex2json.nodes import ASTNode
from latex2json.nodes.base_nodes import TextNode
from latex2json.nodes.math_nodes import EquationNode
from latex2json.parser.parser_core import Handler, ParserCore
from latex2json.latex_maps.fonts import (
    FontStyle,
    LEGACY_TO_FONT_STYLE,
    LATEX_TO_FONT_STYLE,
    TEXT_MODE_COMMANDS,
    FontStyleType,
)
from latex2json.tokens.types import Token


def make_legacy_text_handler(style: FontStyle) -> Handler:
    def legacy_text_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
        parser.set_font(style)
        return []

    return legacy_text_handler


def merge_nodes_in_mathmode_text(
    text_str_decorator: str, nodes: List[ASTNode]
) -> List[ASTNode]:
    r"""e.g. text_str_decorator = \textbf or \raisebox{1in} etc"""
    out_nodes = []
    str_buffer = ""
    for node in nodes:
        if isinstance(node, TextNode):
            if node.text.strip():
                str_buffer += node.text
            continue
        elif isinstance(node, EquationNode):
            str_buffer += node.detokenize()
            continue

        if str_buffer:
            out_nodes.append(TextNode(text_str_decorator + "{%s}" % (str_buffer)))
            str_buffer = ""
        out_nodes.append(node)
    if str_buffer:
        out_nodes.append(TextNode(text_str_decorator + "{%s}" % (str_buffer)))
    return out_nodes


def make_text_handler(style: Optional[FontStyle] = None) -> Handler:
    def text_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
        parser.skip_whitespace()
        if parser.is_math_mode:
            # we need to push textmode to handle e.g. $.. \textbf{...$1+1$...} .. $
            parser.push_mode(ProcessingMode.TEXT)
            nodes = parser.parse_brace_as_nodes()
            parser.pop_mode()
            if not nodes:
                return []

            cmd_name = token.to_str()  # e.g. '\textbf'
            return merge_nodes_in_mathmode_text(cmd_name, nodes)
        else:
            nodes = parser.parse_brace_as_nodes()
            if not nodes:
                return []
            if style:
                for node in nodes:
                    # Use the frontend style mapping for consistent CSS-like values
                    node.add_styles([style.value], insert_at_front=True)
            return nodes

    return text_handler


def textcolor_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
    color_name = parser.parse_color_name()
    if not color_name:
        parser.logger.warning("Warning: \\textcolor expects a color name")
        return []

    if parser.is_math_mode:
        # we need to push textmode to handle e.g. $.. \textcolor{red}{...$1+1$...} .. $
        parser.push_mode(ProcessingMode.TEXT)
        nodes = parser.parse_brace_as_nodes()
        parser.pop_mode()
        if not nodes:
            return []

        cmd_name = token.to_str()  # '\textcolor'
        # if mathmode, we wrap it as one single TextNode containing the raw string
        return merge_nodes_in_mathmode_text(cmd_name + "{%s}" % (color_name), nodes)
    else:
        nodes = parser.parse_brace_as_nodes()
        if not nodes:
            return []
        for node in nodes:
            node.add_styles(["color=" + color_name], insert_at_front=True)
        return nodes


def legacy_color_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
    color_name = parser.parse_color_name()
    if not color_name:
        parser.logger.warning("Warning: \\color expects a color name")
        return []

    parser.set_font(FontStyle(FontStyleType.COLOR, color_name))
    return []


def reset_color_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
    parser.state.reset_font_color()
    return []


def citetext_handler(parser: ParserCore, token: Token) -> Optional[List[ASTNode]]:
    parser.skip_whitespace()
    return parser.parse_brace_as_nodes()


def say_handler(parser: ParserCore, token: Token) -> Optional[List[ASTNode]]:
    parser.skip_whitespace()
    nodes = parser.parse_brace_as_nodes() or []
    return [TextNode('"'), *nodes, TextNode('"')]


def register_text_handlers(parser: ParserCore):
    """
    Register text handling.
    Most of the handlers are only registered in text mode.
    Leave math-mode for katex
    """

    # Register legacy handlers
    # set textmode only for legacy handlers since katex should be able to handle math mode
    for cmd, style_obj in LEGACY_TO_FONT_STYLE.items():
        parser.register_handler(
            cmd, make_legacy_text_handler(style_obj), text_mode_only=True
        )
    parser.register_handler("color", legacy_color_handler, text_mode_only=True)
    parser.register_handler("normalcolor", reset_color_handler, text_mode_only=True)

    # Register handlers for commands that have FontStyle objects
    for cmd, style_obj in LATEX_TO_FONT_STYLE.items():
        handler = make_text_handler(style_obj)
        if cmd in TEXT_MODE_COMMANDS:
            parser.register_handler(cmd, handler)
        else:
            # if no textmode switch, we only need to run it in textmode
            parser.register_handler(cmd, handler, text_mode_only=True)
    parser.register_handler("text", make_text_handler(None))

    # Color handlers
    parser.register_handler("textcolor", textcolor_handler)

    # citetext
    parser.register_handler("citetext", citetext_handler)

    # other
    for backslash in ["backslash", "textbackslash", "arraybackslash"]:
        parser.register_handler(
            backslash, lambda parser, token: [TextNode(r"\\")], text_mode_only=True
        )

    parser.register_handler("indent", lambda parser, token: [TextNode("\t")])

    parser.register_handler("say", say_handler)


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

    text = r"""
\begin{equation}
$1+1$ \textbf{aa bb $1+1$ \ref{eq:xx} bold} 2+2
\end{equation}

\begin{equation}
1+1 \ref{eq:xx} bold
\end{equation}
"""

    text = r"""
\say{hello}
"""

    out = parser.parse(text)
    print(out)
