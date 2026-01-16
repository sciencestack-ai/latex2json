"""
expl3 grouping handlers.

Handles \group_begin:, \group_end:, etc.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token, TokenType


def group_begin_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \group_begin:  ->  \begingroup
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "begingroup")])
    return []


def group_end_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \group_end:  ->  \endgroup
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "endgroup")])
    return []


def register_group_handlers(expander: ExpanderCore) -> None:
    """Register grouping handlers."""
    expander.register_handler("\\group_begin:", group_begin_handler, is_global=True)
    expander.register_handler("\\group_end:", group_end_handler, is_global=True)
