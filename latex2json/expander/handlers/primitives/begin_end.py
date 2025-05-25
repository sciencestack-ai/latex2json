from dataclasses import dataclass
from typing import List, Optional, Tuple
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token, TokenType


# def return_begin_end_tokens(
#     expander: ExpanderCore, prefix: str, name: str
# ) -> List[Token]:
#     return [
#         Token(TokenType.CONTROL_SEQUENCE, prefix),
#         BEGIN_BRACE_TOKEN.copy(),
#         *expander.convert_str_to_tokens(name),
#         END_BRACE_TOKEN.copy(),
#     ]


def begin_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    prefix = "\\begin"
    expander.push_scope()

    name = expander.parse_environment_name()
    if name is None:
        expander.logger.warning(
            f"Warning: {prefix} expects an environment name, but found {expander.peek()}"
        )
        return None

    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, name)])

    return []


def end_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    prefix = "\\end"
    expander.pop_scope()

    name = expander.parse_environment_name()
    if name is None:
        expander.logger.warning(
            f"Warning: {prefix} expects an environment name, but found {expander.peek()}"
        )
        return None

    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "end" + name)])

    return []


def register_begin_end(expander: ExpanderCore):
    expander.register_handler("\\begin", begin_handler, is_global=True)
    expander.register_handler("\\end", end_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    expander.expand(r"\newenvironment{env}[1]{START #1}{END}")
    out = expander.expand(r"\begin{env}{ARG1}TEST\end{env}")
