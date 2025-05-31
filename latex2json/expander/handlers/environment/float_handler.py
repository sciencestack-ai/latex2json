from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token, TokenType


def is_begin_float_token(token: Token) -> bool:
    return token.type == TokenType.CONTROL_SEQUENCE and token.value == "@float"


def is_end_float_token(token: Token) -> bool:
    return token.type == TokenType.CONTROL_SEQUENCE and token.value == "end@float"


def float_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle float tokens."""
    expander.skip_whitespace()
    env_name_tokens = expander.parse_brace_as_tokens()
    if not env_name_tokens:
        expander.logger.warning("\\@float: Missing environment name")
        return None

    # parse the corresponding \end@float too
    body_tokens = expander.parse_begin_end_as_tokens(
        begin_predicate=is_begin_float_token,
        end_predicate=is_end_float_token,
        check_first_token=False,
    )

    env_brace_tokens = [
        BEGIN_BRACE_TOKEN.copy(),
        *env_name_tokens,
        END_BRACE_TOKEN.copy(),
    ]

    # push back to stream as \begin{env_name}...\end{env_name}
    begin_env_token = Token(TokenType.CONTROL_SEQUENCE, "begin")
    end_env_token = Token(TokenType.CONTROL_SEQUENCE, "end")
    out_tokens = [
        begin_env_token,
        *env_brace_tokens,
        *body_tokens,
        end_env_token,
        *env_brace_tokens,
    ]
    expander.push_tokens(out_tokens)
    return []


def register_float_handler(expander: ExpanderCore):
    r"""Register the \@namedef command with the expander."""
    expander.register_macro(
        "\\@float",
        Macro("\\@float", float_handler),
        is_global=True,
    )

    # wild \end@float should not happen if parsed properly
    expander.register_handler("\\end@float", lambda expander, token: [], is_global=True)


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
