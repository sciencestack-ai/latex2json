from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.environment.environment_utils import (
    create_environment_start_token,
    create_environment_end_token,
)
from latex2json.tokens.types import Token


def float_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \@float tokens.

    Returns token directly instead of using push_tokens [\begin] to avoid infinite recursion,
    since our impl deviates from latex in that \begin is directly evaluated instead of \begin->@float tex behavior
    """
    expander.skip_whitespace()
    env_name = expander.parse_brace_name()
    if not env_name:
        expander.logger.warning("\\@float: Missing environment name")
        return None

    expander.push_env_stack(env_name, opening_token=token)

    begin_token = create_environment_start_token(expander, env_name)

    return [begin_token]


def endfloat_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \end@float tokens."""
    # Find the matching @float entry
    matching_entry = expander.find_env_entry("@float")
    if not matching_entry:
        expander.logger.warning("\\end@float: No matching \\@float found")
        return []

    # Pop by exact entry reference
    env_name = expander.pop_env_stack(matching_entry)
    if not env_name:
        expander.logger.warning("\\end@float: Failed to pop environment")
        return []

    end_token = create_environment_end_token(env_name)

    return [end_token]


def dblfloat_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \@dblfloat tokens.

    Double-column floats in two-column documents.
    """
    expander.skip_whitespace()
    env_name = expander.parse_brace_name()
    if not env_name:
        expander.logger.warning("\\@dblfloat: Missing environment name")
        return None

    expander.push_env_stack(env_name, opening_token=token)

    begin_token = create_environment_start_token(expander, env_name)

    return [begin_token]


def enddblfloat_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \end@dblfloat tokens."""
    # Find the matching @dblfloat entry
    matching_entry = expander.find_env_entry("@dblfloat")
    if not matching_entry:
        expander.logger.warning("\\end@dblfloat: No matching \\@dblfloat found")
        return []

    # Pop by exact entry reference
    env_name = expander.pop_env_stack(matching_entry)
    if not env_name:
        expander.logger.warning("\\end@dblfloat: Failed to pop environment")
        return []

    end_token = create_environment_end_token(env_name)

    return [end_token]


def register_float_handler(expander: ExpanderCore):
    r"""Register float and dblfloat handlers with the expander."""
    expander.register_handler(
        "\\@float",
        float_handler,
        is_global=True,
    )
    expander.register_handler("\\end@float", endfloat_handler, is_global=True)

    expander.register_handler(
        "\\@dblfloat",
        dblfloat_handler,
        is_global=True,
    )
    expander.register_handler("\\end@dblfloat", enddblfloat_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_float_handler(expander)
    text = r"""
\makeatletter
\@float{figure}[htb][ss]
    \caption{FIGURE}
\end@float
\makeatother
"""
    out = expander.expand(text)
