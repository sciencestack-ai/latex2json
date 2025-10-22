from typing import List, Optional
from latex2json.nodes.base_nodes import CommandNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token, TokenType


def ignorespaces_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    return []


def linebreak_handler(parser: ParserCore, token: Token):
    """Return as a command node for parser postprocessing later"""
    parser.skip_whitespace()
    parser.parse_bracket_as_nodes()
    return [CommandNode("newline")]


def make_space_command(command: str):
    is_smart_space = command == "xspace"

    def spacecommand_handler(parser: ParserCore, token: Token):
        if is_smart_space:
            next_tok = parser.peek()
            is_next_alpha = (
                next_tok
                and next_tok.type == TokenType.CHARACTER
                and next_tok.value.isalpha()
            )
            if not is_next_alpha:
                return []
        return [CommandNode("space")]

    return spacecommand_handler


def newline_handler(parser: ParserCore, token: Token):
    """Return as a command node for parser postprocessing later"""
    return [CommandNode("newline")]


def hspace_handler(parser: ParserCore, token: Token) -> Optional[List[Token]]:
    """Return as a command node for parser postprocessing later"""
    parser.parse_asterisk()
    parser.skip_whitespace()
    parser.parse_brace_as_nodes()

    return [CommandNode("space")]


def vspace_handler(parser: ParserCore, token: Token) -> Optional[List[Token]]:
    """Return as a command node for parser postprocessing later"""
    parser.parse_asterisk()
    parser.skip_whitespace()
    parser.parse_brace_as_nodes()

    return [CommandNode("newline")]


def register_spacing_handlers(parser: ParserCore):
    for cmd in ["ignorespaces", "noindent"]:
        parser.register_handler(cmd, ignorespaces_handler)

    # allowbreak is only useful in pdf
    for cmd in ["allowbreak"]:
        parser.register_handler(cmd, lambda parser, token: [])

    parser.register_handler(
        "linebreak",
        linebreak_handler,
    )

    for newline in [
        "newline",
        "@centercr",
        "par",
        "pagebreak",
        "filbreak",
        "eject",
        "newpage",
        "goodbreak",
        "smallbreak",
        "medbreak",
        "bigbreak",
        "break",
        "smallskip",
        "medskip",
        "bigskip",
    ]:
        parser.register_handler(
            newline,
            newline_handler,
        )

    for space in [
        "quad",
        "qquad",
        "xspace",
        "space",
        "enspace",
        "thinspace",
        ",",
        ";",
        ":",
        "!",
        " ",
    ]:
        parser.register_handler(
            space,
            make_space_command(space),
            text_mode_only=True,
        )

    for hspace in ["hphantom", "phantom", "hspace", "linespread"]:
        parser.register_handler(
            hspace,
            hspace_handler,
        )

    for vspace in ["vphantom", "vspace", "addvspace"]:
        parser.register_handler(
            vspace,
            vspace_handler,
        )

    # register_ignore_handlers_util(parser, spacing_patterns)
