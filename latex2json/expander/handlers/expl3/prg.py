"""
expl3 programming (prg) utilities.

Handles \prg_return_true:, \prg_return_false:, \prg_do_nothing:, etc.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def prg_return_true_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \prg_return_true:  ->  used in predicates, expands to nothing meaningful here
    """
    return []


def prg_return_false_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \prg_return_false:  ->  used in predicates, expands to nothing meaningful here
    """
    return []


def prg_do_nothing_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \prg_do_nothing:  ->  expands to nothing
    """
    return []


def register_prg_handlers(expander: ExpanderCore) -> None:
    """Register programming utility handlers."""
    expander.register_handler(
        "\\prg_return_true:", prg_return_true_handler, is_global=True
    )
    expander.register_handler(
        "\\prg_return_false:", prg_return_false_handler, is_global=True
    )
    expander.register_handler(
        "\\prg_do_nothing:", prg_do_nothing_handler, is_global=True
    )
