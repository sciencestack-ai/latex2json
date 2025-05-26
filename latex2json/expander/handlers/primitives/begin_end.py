from dataclasses import dataclass
from typing import List, Optional, Tuple
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token, TokenType


def begin_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    prefix = "\\begin"
    expander.push_scope()

    name = expander.parse_environment_name()
    if name is None:
        expander.logger.warning(
            f"Warning: {prefix} expects an environment name, but found {expander.peek()}"
        )
        return None

    env_def = expander.state.get_environment_definition(name)
    if not env_def:
        expander.logger.info(
            f"{prefix}{{{name}}} not found, returning default environment start token"
        )
    elif env_def.begin_handler:
        return env_def.begin_handler(expander, token)
    else:
        # env is defined but has no begin handler
        expander.logger.info(
            f"Warning: {prefix}{{{name}}} has no begin handler, returning default environment start token"
        )

    begin_token = Token(TokenType.ENVIRONMENT_START, name)
    if expander.state.has_counter(name):
        begin_token.numbering = expander.state.get_counter_as_format(name)

    return [begin_token]


def end_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    prefix = "\\end"
    expander.pop_scope()

    name = expander.parse_environment_name()
    if name is None:
        expander.logger.warning(
            f"Warning: {prefix} expects an environment name, but found {expander.peek()}"
        )
        return None

    env_def = expander.state.get_environment_definition(name)
    if not env_def:
        expander.logger.info(
            f"{prefix}{{{name}}} not found, returning default environment end token"
        )
    elif env_def.end_handler:
        return env_def.end_handler(expander, token)
    else:
        # env is defined but has no end handler
        expander.logger.info(
            f"Warning: {prefix}{{{name}}} has no end handler, returning default environment end token"
        )

    return [Token(TokenType.ENVIRONMENT_END, name)]


def register_begin_end(expander: ExpanderCore):
    expander.register_handler("\\begin", begin_handler, is_global=True)
    expander.register_handler("\\end", end_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    expander.expand(r"\newenvironment{env}[1]{START #1}{END}")
    out = expander.expand(r"\begin{env}{ARG1}TEST\end{env}")
