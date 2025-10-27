from dataclasses import dataclass
from typing import List, Optional, Tuple
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.environment.environment_utils import (
    create_environment_start_token,
    create_environment_end_token,
)
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import (
    EnvironmentEndToken,
    EnvironmentStartToken,
    EnvironmentType,
    Token,
    TokenType,
)


def begin_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    prefix = "\\begin"

    name = expander.parse_brace_name()
    if name is None:
        expander.logger.warning(
            f"{prefix} expects an environment name, but found {expander.peek()}"
        )
        return None

    expander.push_scope()
    expander.push_env_stack(name, opening_token=token)

    env_def = expander.state.get_environment_definition(name)

    if not env_def:
        log_str = f"Environment '{name}' not found -> "
        if expander.get_macro(name):
            log_str += f"Found \\{name} instead"
            # convert to macro
            expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, name)])
        else:
            log_str += " returning default env"
            # strip out any unknown env optional arg if exists
            expander.skip_whitespace()
            bracket_tokens = expander.parse_bracket_as_tokens()
            if bracket_tokens is not None:
                log_str += (
                    f" -> parsed [{expander.convert_tokens_to_str(bracket_tokens)}]"
                )
        expander.logger.info(log_str)
    elif env_def.begin_handler:
        return env_def.begin_handler(expander, token)
    else:
        # env is defined but has no begin handler
        expander.logger.info(
            f"{prefix}{{{name}}} has no begin handler, returning default env"
        )

    begin_token = create_environment_start_token(expander, name)

    return [begin_token]


def end_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    prefix = "\\end"

    name = expander.parse_brace_name()
    if name is None:
        expander.logger.warning(
            f"{prefix} expects an environment name, but found {expander.peek()}"
        )
        return None

    env_def = expander.state.get_environment_definition(name)

    out_tokens = [create_environment_end_token(name)]

    if not env_def:
        expander.logger.info(
            f"{prefix}{{{name}}} not found, returning default environment end token"
        )
    elif env_def.end_handler:
        out_tokens = env_def.end_handler(expander, token)
    else:
        # env is defined but has no end handler
        expander.logger.info(
            f"{prefix}{{{name}}} has no end handler, returning default environment end token"
        )

    # pop scope at the end!
    expander.pop_env_stack(name)
    expander.pop_scope()

    return out_tokens


def register_begin_end(expander: ExpanderCore):
    expander.register_handler("\\begin", begin_handler, is_global=True)
    expander.register_handler("\\end", end_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    expander.expand(r"\newenvironment{env}[1]{START #1}{END}")
    out = expander.expand(r"\begin{env}{ARG1}TEST\end{env}")
