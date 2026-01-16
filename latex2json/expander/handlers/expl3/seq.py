"""
expl3 sequence (seq) handlers.

Handles \seq_new:N, \seq_clear:N, and related functions.
Future: \seq_put_right:Nn, \seq_map_inline:Nn, \seq_use:Nnnn, etc.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType


def seq_new_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \seq_new:N \l_my_seq  ->  \def\l_my_seq{}
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


def seq_clear_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \seq_clear:N \l_my_seq  ->  \def\l_my_seq{}
    """
    return seq_new_handler(expander, _token)


def register_seq_handlers(expander: ExpanderCore) -> None:
    """Register sequence handlers."""
    for name in ["\\seq_new:N", "\\seq_clear_new:N"]:
        expander.register_handler(name, seq_new_handler, is_global=True)
    for name in ["\\seq_clear:N", "\\seq_gclear:N"]:
        expander.register_handler(name, seq_clear_handler, is_global=True)
