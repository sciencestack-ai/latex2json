"""
expl3 comma list (clist) handlers.

Handles \clist_new:N, \clist_clear:N, and related functions.
Future: \clist_map_inline:Nn, \clist_set:Nn, etc.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType


def clist_new_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \clist_new:N \l_my_clist  ->  \def\l_my_clist{}
    """
    expander.skip_whitespace()
    var = expander.consume()
    if var:
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
                Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
                Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
            ]
        )
    return []


def clist_clear_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_clear:N \l_my_clist  ->  \def\l_my_clist{}
    """
    return clist_new_handler(expander, _token)


def register_clist_handlers(expander: ExpanderCore) -> None:
    """Register comma list handlers."""
    for name in ["\\clist_new:N", "\\clist_clear_new:N"]:
        expander.register_handler(name, clist_new_handler, is_global=True)
    for name in ["\\clist_clear:N", "\\clist_gclear:N"]:
        expander.register_handler(name, clist_clear_handler, is_global=True)
