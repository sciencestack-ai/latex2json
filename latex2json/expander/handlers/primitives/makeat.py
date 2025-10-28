from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token


def make_at_letter_handler(
    expander: ExpanderCore, token: Token
) -> Optional[List[Token]]:
    expander.makeatletter()
    return []


def make_at_other_handler(
    expander: ExpanderCore, token: Token
) -> Optional[List[Token]]:
    expander.makeatother()
    return []


def make_catcode_handler(
    catcode: Catcode, command_name: str
):
    """Factory function to create catcode handlers for @make* commands"""
    def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        expander.skip_whitespace()
        tok = expander.consume()
        if tok is None:
            expander.logger.warning(f"{command_name} expected character, but found None")
            return []

        char = tok.value
        if len(char) > 1:
            char = char[0]
            expander.logger.warning(f"{command_name} only takes one character, using {char}")

        expander.set_catcode(ord(char), catcode)
        return []

    return handler


def register_makeat(expander: ExpanderCore):
    expander.register_handler("\\makeatletter", make_at_letter_handler, is_global=True)
    expander.register_handler("\\makeatother", make_at_other_handler, is_global=True)
    expander.register_handler(
        "\\@makeletter", make_catcode_handler(Catcode.LETTER, "\\@makeletter"), is_global=True
    )
    expander.register_handler(
        "\\@makeother", make_catcode_handler(Catcode.OTHER, "\\@makeother"), is_global=True
    )
    expander.register_handler(
        "\\@makeescape", make_catcode_handler(Catcode.ESCAPE, "\\@makeescape"), is_global=True
    )
