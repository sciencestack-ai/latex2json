from dataclasses import dataclass
from typing import List, Optional, Tuple
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token, TokenType


def begin_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    prefix = "\\begin"
    expander.push_scope()

    out = expander.parse_environment_name()
    if out is None:
        expander.logger.warning(
            f"Warning: {prefix} expects an environment name, but found {expander.peek()}"
        )
        return None

    name, has_asterisk = out

    env_def = expander.state.get_environment_definition(name)
    if not env_def:
        expander.logger.info(
            f"{prefix}{{{name}}} not found, returning default environment start token"
        )
    elif env_def.has_direct_command:
        # if has asterisk, use begin_handler directly
        if has_asterisk and env_def.begin_handler:
            return env_def.begin_handler(expander, token, has_asterisk=True)
        expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, name)])
        return []
    elif env_def.begin_handler:
        return env_def.begin_handler(expander, token, has_asterisk=has_asterisk)
    else:
        # env is defined but has no begin handler
        expander.logger.info(
            f"Warning: {prefix}{{{name}}} has no begin handler, returning default environment start token"
        )

    return [Token(TokenType.ENVIRONMENT_START, name, has_asterisk=has_asterisk)]


def end_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    prefix = "\\end"
    expander.pop_scope()

    out = expander.parse_environment_name()
    if out is None:
        expander.logger.warning(
            f"Warning: {prefix} expects an environment name, but found {expander.peek()}"
        )
        return None

    name, has_asterisk = out

    env_def = expander.state.get_environment_definition(name)
    if not env_def:
        expander.logger.info(
            f"{prefix}{{{name}}} not found, returning default environment end token"
        )
    elif env_def.has_direct_command:
        if has_asterisk and env_def.end_handler:
            return env_def.end_handler(expander, token, has_asterisk=True)
        expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "end" + name)])
        return []
    elif env_def.end_handler:
        return env_def.end_handler(expander, token, has_asterisk=has_asterisk)
    else:
        # env is defined but has no end handler
        expander.logger.info(
            f"Warning: {prefix}{{{name}}} has no end handler, returning default environment end token"
        )

    return [Token(TokenType.ENVIRONMENT_END, name, has_asterisk=has_asterisk)]


def register_begin_end(expander: ExpanderCore):
    expander.register_handler("\\begin", begin_handler, is_global=True)
    expander.register_handler("\\end", end_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    expander.expand(r"\newenvironment{env}[1]{START #1}{END}")
    out = expander.expand(r"\begin{env}{ARG1}TEST\end{env}")
