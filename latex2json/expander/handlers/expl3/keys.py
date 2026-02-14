r"""
expl3 keys (l3keys) handlers.

Handles \keys_define:nn, \keys_set:nn, \keys_if_exist:nnTF, etc.
The l3keys module provides a key-value interface similar to keyval/xkeyval.

For our parsing purposes, we mostly consume and ignore key definitions
since we're extracting content, not executing typesetting.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def keys_define_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \keys_define:nn {module} {key definitions}
    Defines keys for a module. We consume and ignore this.
    """
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # module name
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # key definitions
    return []


def keys_set_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \keys_set:nn {module} {key=value pairs}
    Sets keys for a module. We consume and ignore this.
    """
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # module name
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # key-value pairs
    return []


def keys_if_exist_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \keys_if_exist:nnTF {module} {key} {true} {false}
    Tests if a key exists. Since we don't track keys, always take false branch.
    """
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # module name
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # key name
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # true branch (ignore)
    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []
    expander.push_tokens(false_branch)
    return []


def register_keys_handlers(expander: ExpanderCore) -> None:
    """Register l3keys handlers."""
    # Key definition
    for name in ["\\keys_define:nn", "\\keys_define:nx"]:
        expander.register_handler(name, keys_define_handler, is_global=True)

    # Key setting
    for name in [
        "\\keys_set:nn",
        "\\keys_set:nV",
        "\\keys_set:nv",
        "\\keys_set:nx",
        "\\keys_set:no",
    ]:
        expander.register_handler(name, keys_set_handler, is_global=True)

    # Existence tests
    expander.register_handler(
        "\\keys_if_exist:nnTF", keys_if_exist_TF_handler, is_global=True
    )
