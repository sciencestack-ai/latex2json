from typing import List, Optional
from latex2json.nodes.base_nodes import CommandNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import WHITESPACE_TOKEN, Token, TokenType
from latex2json.tokens.utils import is_whitespace_token


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
    parser.register_handler(
        "\\ignorespaces",
        ignorespaces_handler,
    )

    parser.register_handler(
        "\\linebreak",
        linebreak_handler,
    )

    for newline in [
        "newline",
        "pagebreak",
        "filbreak",
        "newpage",
        "allowbreak",
        "goodbreak",
        "smallbreak",
        "medbreak",
        "bigbreak",
        "break",
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

    for vspace in ["vphantom", "vspace"]:
        parser.register_handler(
            vspace,
            vspace_handler,
        )

    # register_ignore_handlers_util(parser, spacing_patterns)
