from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.types import WHITESPACE_TOKEN, Token, TokenType


def ignorespaces_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    return []


def break_handler(expander: ExpanderCore, token: Token):
    return [Token(TokenType.END_OF_LINE, "\n")]


def linebreak_handler(expander: ExpanderCore, token: Token):
    expander.parse_bracket_as_tokens(expand=True)
    return [Token(TokenType.END_OF_LINE, "\n")]


def regular_space_handler(
    expander: ExpanderCore, token: Token
) -> Optional[List[Token]]:
    return [WHITESPACE_TOKEN.copy()]


def hphantom_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    expander.parse_brace_as_tokens(expand=True)

    return [WHITESPACE_TOKEN.copy()]


def vphantom_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    expander.parse_brace_as_tokens(expand=True)

    return [Token(TokenType.END_OF_LINE, "\n")]


def register_spacing_handlers(expander: ExpanderCore):
    expander.register_handler(
        "\\ignorespaces",
        ignorespaces_handler,
        is_global=True,
    )

    for linebreak in [
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
        expander.register_handler(
            linebreak,
            break_handler,
            is_global=True,
        )

    for space in [
        "quad",
        "qquad",
        "xspace",
        "space",
        "thinspace",
    ]:  # , ",", ";", ":", "!"]:
        expander.register_handler(
            space,
            regular_space_handler,
            is_global=True,
        )

    for hspace in ["hphantom", "phantom", "hspace", "linespread"]:
        expander.register_handler(
            hspace,
            hphantom_handler,
            is_global=True,
        )

    for vspace in ["vphantom", "vspace"]:
        expander.register_handler(
            vspace,
            vphantom_handler,
            is_global=True,
        )

    # register_ignore_handlers_util(expander, spacing_patterns)
