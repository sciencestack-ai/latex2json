from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import (
    Token,
    BEGIN_BRACKET_TOKEN,
    END_BRACKET_TOKEN,
    BEGIN_BRACE_TOKEN,
    END_BRACE_TOKEN,
    TokenType,
)


def is_endenv_command(token: Token, env_name: str) -> bool:
    return token.type == TokenType.CONTROL_SEQUENCE and token.value == f"end{env_name}"


def process_env_block(expander: ExpanderCore, env_name: str) -> Optional[List[Token]]:
    tok = expander.peek()
    if tok is None:
        return None

    predicate = lambda tok: is_endenv_command(tok, env_name)
    block = expander.process(predicate)

    tok = expander.peek()
    if tok and is_endenv_command(tok, env_name):
        expander.consume()

    return block


def environment_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    env_name = token.value
    block = process_env_block(expander, env_name)
    if block is None:
        expander.logger.warning(
            f"Warning: \\begin{{{env_name}}} expects \\end{{{env_name}}}"
        )
        return None

    output_tokens: List[Token] = [Token(TokenType.ENVIRONMENT_START, env_name)]
    output_tokens.extend(block)
    output_tokens.append(Token(TokenType.ENVIRONMENT_END, env_name))
    return output_tokens


def register_base_environment_handlers(expander: ExpanderCore):
    for env_name in ["document"]:
        expander.register_macro(
            env_name,
            Macro(env_name, environment_handler, []),
            is_global=True,
        )
        end_env_name = f"end{env_name}"
        expander.register_macro(
            end_env_name,
            Macro(end_env_name, lambda *args: [], []),
            is_global=True,
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_base_environment_handlers(expander)
    # out = expander.expand(r"\begin{document}Hello\end{document}")
    expander.expand(r"\newenvironment{test}[1]{BEGIN #1 123}{END}")
    out = expander.expand(r"\begin{test}{ABC}CONTENT\end{test}")
