r"""
expl3 use handlers.

Handles \use:n, \use_none:n, etc.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def use_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \use:n {tokens}  ->  tokens (identity)
    """
    expander.skip_whitespace()
    tokens = expander.parse_brace_as_tokens() or []
    expander.push_tokens(tokens)
    return []


def use_none_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \use_none:n {tokens}  ->  (discard)
    """
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()
    return []


def register_use_handlers(expander: ExpanderCore) -> None:
    """Register use handlers."""
    expander.register_handler("\\use:n", use_handler, is_global=True)
    for name in ["\\use_none:n", "\\use_none:nn"]:
        expander.register_handler(name, use_none_handler, is_global=True)
