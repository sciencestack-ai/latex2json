"""
expl3 quark handlers.

Handles \q_no_value, \quark_if_no_value:NTF, etc.
Quarks are special marker tokens used in expl3 for signaling special values.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token, TokenType


def quark_if_no_value_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \quark_if_no_value:NTF \token {true} {false}
    """
    expander.skip_whitespace()
    var = expander.consume()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    # Check if it's \q_no_value
    is_no_value = False
    if var and var.type == TokenType.CONTROL_SEQUENCE:
        is_no_value = var.value == "q_no_value"

    if is_no_value:
        expander.push_tokens(true_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def register_quark_handlers(expander: ExpanderCore) -> None:
    """Register quark handlers."""
    expander.register_handler(
        "\\quark_if_no_value:NTF", quark_if_no_value_TF_handler, is_global=True
    )
