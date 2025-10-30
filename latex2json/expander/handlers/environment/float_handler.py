from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.environment.environment_utils import (
    begin_environment_handler,
    create_environment_end_token,
)
from latex2json.tokens.types import Token


def float_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \@float tokens.

    Returns token directly instead of using push_tokens [\begin] to avoid infinite recursion,
    since our impl deviates from latex in that \begin is directly evaluated instead of \begin->@float tex behavior
    """
    return begin_environment_handler(expander, token, check_env_handler=False)


def _end_float_common(
    expander: ExpanderCore, env_type: str, end_cmd: str
) -> Optional[List[Token]]:
    r"""Common handler for \end@float and \end@dblfloat tokens.

    Args:
        expander: The expander instance
        env_type: The environment type to search for ("@float" or "@dblfloat")
        end_cmd: The end command name for logging ("\end@float" or "\end@dblfloat")
    """
    # Find the matching entry
    matching_entry = expander.find_env_entry(env_type)
    if not matching_entry:
        expander.logger.warning(f"{end_cmd}: No matching \\{env_type} found")
        return []

    # Pop by exact entry reference
    env_name = expander.pop_env_stack(matching_entry)
    if not env_name:
        expander.logger.warning(f"{end_cmd}: Failed to pop environment")
        return []

    expander.pop_scope()

    end_token = create_environment_end_token(env_name)

    return [end_token]


def endfloat_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    return _end_float_common(expander, "@float", "\\end@float")


def dblfloat_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    return begin_environment_handler(expander, token, check_env_handler=False)


def enddblfloat_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    return _end_float_common(expander, "@dblfloat", "\\end@dblfloat")


def continued_float_handler(
    expander: ExpanderCore, token: Token
) -> Optional[List[Token]]:
    r"""Handle \\ContinuedFloat command.

    LIMITATION: In real LaTeX, \\ContinuedFloat causes the next caption to continue
    the numbering from the previous float (e.g., Figure 1 followed by Figure 1 (continued)).
    Our implementation currently ignores this command, so continued floats receive new
    numbering instead of continuing the previous float's numbering. This is a limitation
    of the single-pass architecture where we cannot easily track and restore previous
    float counter states.
    """
    # hack: decrement current float so that next float will be numbered the same
    parent_float_env = expander.get_parent_float_env()
    # if parent_float_env and parent_float_env.counter_name:
    #     expander.state.add_to_counter(parent_float_env.counter_name, -1)
    return []


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

    expander.register_handler(
        "\\ContinuedFloat", continued_float_handler, is_global=True
    )


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
