r"""
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


def prg_replicate_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \prg_replicate:nn {count} {code}  ->  repeats {code} {count} times

    Examples:
    - \prg_replicate:nn {3} {x}  -> xxx
    - \prg_replicate:nn {0} {x}  -> (nothing)
    - \prg_replicate:nn {2} {ab} -> abab
    """
    expander.skip_whitespace()
    count_tokens = expander.parse_brace_as_tokens() or []
    count_str = "".join(t.value for t in count_tokens).strip()

    expander.skip_whitespace()
    code_tokens = expander.parse_brace_as_tokens() or []

    try:
        count = int(count_str)
    except ValueError:
        return []

    if count <= 0:
        return []

    # Replicate the code tokens
    result = []
    for _ in range(count):
        result.extend([t.copy() for t in code_tokens])

    expander.push_tokens(result)
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
    expander.register_handler(
        "\\prg_replicate:nn", prg_replicate_handler, is_global=True
    )
