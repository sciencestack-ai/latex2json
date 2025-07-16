from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import (
    EnvironmentStartToken,
    EnvironmentType,
    Token,
    TokenType,
)


def is_begin_float_token(token: Token) -> bool:
    return token.type == TokenType.CONTROL_SEQUENCE and token.value == "@float"


def is_end_float_token(token: Token) -> bool:
    return token.type == TokenType.CONTROL_SEQUENCE and token.value == "end@float"


def float_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle float tokens."""
    expander.skip_whitespace()
    env_name = expander.parse_brace_name()
    if not env_name:
        expander.logger.warning("\\@float: Missing environment name")
        return None

    expander.state.push_env_stack(env_name)

    env_def = expander.get_environment_definition(env_name)

    display_name = env_name
    env_type = EnvironmentType.DEFAULT
    if env_def:
        display_name = env_def.display_name
        env_type = env_def.env_type
    begin_token = EnvironmentStartToken(
        env_name,
        display_name=display_name,
        env_type=env_type,
    )

    return [begin_token]


def endfloat_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \end@float tokens."""
    env_name = expander.state.pop_env_stack()
    if not env_name:
        expander.logger.warning("\\end@float: No float environment to end")
        return []

    end_token = Token(TokenType.ENVIRONMENT_END, env_name)

    return [end_token]


def register_float_handler(expander: ExpanderCore):
    r"""Register the \@namedef command with the expander."""
    expander.register_handler(
        "\\@float",
        float_handler,
        is_global=True,
    )

    # wild \end@float should not happen if parsed properly
    expander.register_handler("\\end@float", endfloat_handler, is_global=True)


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
