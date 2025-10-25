from typing import List, Optional

from latex2json.expander.state import ProcessingMode
from latex2json.nodes import ASTNode
from latex2json.nodes.base_nodes import CommandNode, TextNode
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
    r"""e.g. text_str_decorator = \textbf or \raisebox{1in} etc

    This function maintains KaTeX compatibility while preserving the node AST structure.

    Goal: Convert text formatting commands (like \textbf, \textcolor) to raw strings that
    KaTeX can render, BUT keep semantic nodes (like CitationNode, RefNode) as separate
    nodes in the AST so they can be processed independently.

    Example:
        Input: \textbf{abc \cite{ref1} $123$}
        Output: [TextNode(\textbf{abc }), CitationNode(...), TextNode(\textbf{$123$})]

        The \textbf formatting is preserved as raw text for KaTeX rendering, but the
        \cite node remains a separate CitationNode for AST processing.
    """
    out_nodes = []
    str_buffer = ""
    for node in nodes:
        # Merge simple nodes (text, equations, commands) into raw string for KaTeX rendering
        if isinstance(node, (EquationNode, CommandNode, TextNode)):
            str_buffer += node.detokenize()
            continue

        # When we hit a semantic node (e.g., RefNode, CitationNode), flush the buffer
        # and keep the semantic node separate in the AST
        if str_buffer:
            out_nodes.append(TextNode(text_str_decorator + "{%s}" % (str_buffer)))
            str_buffer = ""
        out_nodes.append(node)
    if str_buffer:
        out_nodes.append(TextNode(text_str_decorator + "{%s}" % (str_buffer)))
    return out_nodes


def _parse_textcommand_to_nodes(
    parser: ParserCore, text_cmd_name: str, style_value: Optional[str]
) -> List[ASTNode]:
    r"""Parse text commands like \textbf, \textit, \textcolor inside equations.

    When in math mode, we need special handling to maintain KaTeX compatibility:
    - Preserve the text decorator (e.g., \textbf{...}) as raw LaTeX for KaTeX to render
    - BUT extract semantic nodes (CitationNode, RefNode, etc.) to maintain the AST structure

    This allows the equation string to be KaTeX-compatible (e.g., "1+1 \textbf{aa $1+1$ bb} 2+2")
    while keeping non-textual nodes separate for independent processing.

    Test cases that drove this design:
        $$\textbf{aa $1+1$ bb}$$  -> equation_to_str() == r"1+1 \textbf{aa $1+1$ bb} 2+2"
        $$\textbf{abc \cite{ref1}$123$}$$  -> \textbf wraps text but CitationNode stays in AST
    """
    parser.skip_whitespace()
    if parser.is_math_mode:
        parser.push_mode(ProcessingMode.TEXT)
        parser.skip_whitespace()
        nodes = parser.parse_brace_as_nodes()
        parser.pop_mode()
        if not nodes:
            return []

        return merge_nodes_in_mathmode_text(text_cmd_name, nodes)
    else:
        nodes = parser.parse_brace_as_nodes()
        if not nodes:
            return []
        if style_value:
            for node in nodes:
                # Use the frontend style mapping for consistent CSS-like values
                node.add_styles([style_value], insert_at_front=True)
        return nodes


def make_text_handler(style: Optional[FontStyle] = None) -> Handler:
    def text_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
        return _parse_textcommand_to_nodes(
            parser, token.to_str(), style.value if style else None
        )

    return text_handler


def textcolor_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
    color_name = parser.parse_color_name()
    if not color_name:
        parser.logger.info("\\textcolor expects a color name")
        return []

    cmd_name = "%s{%s}" % (token.to_str(), color_name)
    return _parse_textcommand_to_nodes(parser, cmd_name, "color=" + color_name)


def legacy_color_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
    color_name = parser.parse_color_name()
    if not color_name:
        parser.logger.warning("\\color expects a color name")
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
