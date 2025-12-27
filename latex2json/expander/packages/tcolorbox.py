from typing import List, Optional, Tuple
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.expander.handlers.primitives.declarations.newcommand import (
    newcommand_handler,
)
from latex2json.expander.handlers.primitives.declarations.declaration_utils import (
    get_newcommand_args_and_definition,
)
from latex2json.latex_maps.environments import EnvironmentDefinition
from latex2json.tokens.types import (
    BEGIN_BRACKET_TOKEN,
    END_BRACKET_TOKEN,
    Token,
    TokenType,
)
from latex2json.tokens.utils import is_begin_bracket_token


def newtcbox_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    options = expander.parse_bracket_as_tokens()

    out = newcommand_handler(expander, token)
    if out is None:
        return None

    cmd_name = out.cmd_token

    # print(out)

    def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        # Parse exactly num_args arguments
        args = expander.get_parsed_args(
            out.num_args, out.default_arg, command_name=cmd_name
        )
        if args is None:
            return None

        subbed = expander.substitute_token_args(out.definition, args)
        tokens = [Token(TokenType.CONTROL_SEQUENCE, "tcbox")]
        tokens += [BEGIN_BRACKET_TOKEN.copy()]
        tokens += subbed
        tokens += [END_BRACKET_TOKEN.copy()]
        return tokens

    expander.register_handler(cmd_name, handler, is_global=True, is_user_defined=True)

    return []


def newtcolorbox_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""
    Handle \newtcolorbox{name}[num_args][default]{options}

    Creates a new tcolorbox environment. The environment arguments are parsed
    and the options (styling) are ignored for now.

    Example:
        \newtcolorbox{mybox}[2][]{colback=red!5!white, title=#2, #1}

        Creates environment 'mybox' with 2 args (first optional with empty default).
    """
    expander.skip_whitespace()
    # Parse optional initial options [init options] - ignored for now
    _ = expander.parse_bracket_as_tokens()

    # Parse environment name
    env_name = expander.parse_brace_name()
    if env_name is None:
        expander.logger.warning(f"\\newtcolorbox expects an environment name")
        return None

    # Parse [num_args] and optional [default_arg]
    parsed = get_newcommand_args_and_definition(expander)
    if parsed is None:
        expander.logger.warning(
            f"\\newtcolorbox {env_name} expects options in braces"
        )
        return None

    num_args, default_arg, options_tokens = parsed
    # Note: options_tokens contains tcolorbox styling options which we ignore

    env_def = EnvironmentDefinition(
        name=env_name,
        begin_definition=[],  # tcolorbox options are ignored
        end_definition=[],
        num_args=num_args,
        default_arg=default_arg,
        has_direct_command=env_name.isalpha(),
    )

    expander.register_environment(
        env_name, env_def, is_global=True, is_user_defined=True
    )

    return []


def parse_xparse_arg_spec(arg_spec: str) -> Tuple[int, Optional[List[Token]]]:
    """
    Parse xparse-style argument specification.

    Returns (num_args, default_arg) where:
    - num_args: total number of arguments
    - default_arg: default value for first optional argument, or None

    Argument types:
    - m: mandatory argument
    - o: optional argument (no default)
    - O{default}: optional argument with default
    - d<tok1><tok2>: delimited optional argument
    - D<tok1><tok2>{default}: delimited optional with default

    Note: This is a simplified parser that counts arguments and extracts
    the first optional default. Full xparse semantics are not implemented.
    """
    num_args = 0
    default_arg = None
    i = 0
    first_optional_seen = False

    while i < len(arg_spec):
        c = arg_spec[i]

        if c in ' \t\n':
            i += 1
            continue
        elif c == 'm':
            num_args += 1
            i += 1
        elif c == 'o':
            num_args += 1
            if not first_optional_seen:
                first_optional_seen = True
                default_arg = []  # empty default
            i += 1
        elif c == 'O':
            num_args += 1
            i += 1
            # Parse {default}
            if i < len(arg_spec) and arg_spec[i] == '{':
                brace_count = 1
                i += 1
                default_start = i
                while i < len(arg_spec) and brace_count > 0:
                    if arg_spec[i] == '{':
                        brace_count += 1
                    elif arg_spec[i] == '}':
                        brace_count -= 1
                    i += 1
                if not first_optional_seen:
                    first_optional_seen = True
                    # Extract default value as tokens (simplified: just character tokens)
                    default_str = arg_spec[default_start:i-1]
                    if default_str:
                        default_arg = [Token(TokenType.CHARACTER, c) for c in default_str]
                    else:
                        default_arg = []
        elif c in 'dD':
            # Delimited arguments d<tok1><tok2> or D<tok1><tok2>{default}
            num_args += 1
            i += 1
            # Skip the two delimiter characters
            if i < len(arg_spec):
                i += 1  # skip first delimiter
            if i < len(arg_spec):
                i += 1  # skip second delimiter
            if c == 'D' and i < len(arg_spec) and arg_spec[i] == '{':
                # Skip the default value
                brace_count = 1
                i += 1
                while i < len(arg_spec) and brace_count > 0:
                    if arg_spec[i] == '{':
                        brace_count += 1
                    elif arg_spec[i] == '}':
                        brace_count -= 1
                    i += 1
        else:
            # Unknown spec character, skip
            i += 1

    return num_args, default_arg


def declaretcolorbox_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""
    Handle \DeclareTColorBox{name}{arg_spec}{options}

    Creates a new tcolorbox environment with xparse-style argument specification.

    Example:
        \DeclareTColorBox{mytotalbox}{O{}mO{-2mm}}{colback=red, title=#2, #1}

        Creates environment 'mytotalbox' with 3 args:
        - #1: optional with empty default
        - #2: mandatory
        - #3: optional with default "-2mm"
    """
    expander.skip_whitespace()

    # Parse environment name
    env_name = expander.parse_brace_name()
    if env_name is None:
        expander.logger.warning(f"\\DeclareTColorBox expects an environment name")
        return None

    # Parse argument specification {O{}mO{-2mm}}
    expander.skip_whitespace()
    arg_spec_tokens = expander.parse_brace_as_tokens()
    if arg_spec_tokens is None:
        expander.logger.warning(
            f"\\DeclareTColorBox {env_name} expects argument specification in braces"
        )
        return None

    arg_spec = "".join(t.value for t in arg_spec_tokens)
    num_args, default_arg = parse_xparse_arg_spec(arg_spec)

    # Parse options {colback=red, ...} - ignored for now
    expander.skip_whitespace()
    _ = expander.parse_brace_as_tokens()

    env_def = EnvironmentDefinition(
        name=env_name,
        begin_definition=[],  # tcolorbox options are ignored
        end_definition=[],
        num_args=num_args,
        default_arg=default_arg,
        has_direct_command=env_name.isalpha(),
    )

    expander.register_environment(
        env_name, env_def, is_global=True, is_user_defined=True
    )

    return []


def register_tcolorbox(expander: ExpanderCore):
    expander.register_handler("newtcbox", newtcbox_handler, is_global=True)
    expander.register_handler("renewtcbox", newtcbox_handler, is_global=True)

    # tcolorbox environment definition commands
    expander.register_handler("newtcolorbox", newtcolorbox_handler, is_global=True)
    expander.register_handler("renewtcolorbox", newtcolorbox_handler, is_global=True)
    expander.register_handler("DeclareTColorBox", declaretcolorbox_handler, is_global=True)
    expander.register_handler("NewTColorBox", declaretcolorbox_handler, is_global=True)
    expander.register_handler("RenewTColorBox", declaretcolorbox_handler, is_global=True)
    expander.register_handler("ProvideTColorBox", declaretcolorbox_handler, is_global=True)

    ignore_cmds = {
        # tcb
        "tcbset": "{",
        "tcbuselibrary": "{",
    }
    register_ignore_handlers_util(expander, ignore_cmds, expand=False)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    # Test newtcbox
    text = r"""
\newtcbox{\mymath}[1][default]{%
    nobeforeafter, math upper, tcbox raise base,
    enhanced, colframe=blue!30!black,
    colback=green!30, boxrule=1pt,
    #1}

    \mymath{BOX}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print("newtcbox test:")
    print(out_str)
    print()

    # Test newtcolorbox
    expander2 = Expander()
    text2 = r"""
\newtcolorbox{mybox}[2][]{colback=red!5!white,
colframe=red!75!black,fonttitle=\bfseries,
colbacktitle=red!85!black,enhanced,
attach boxed title to top center={yshift=-2mm},
title=#2,#1}

\begin{mybox}[colback=yellow]{Hello there}
This is my own box with a mandatory title and options.
\end{mybox}
""".strip()
    out2 = expander2.expand(text2)
    out_str2 = expander2.convert_tokens_to_str(out2).strip()
    print("newtcolorbox test:")
    print(out_str2)
    print()

    # Test DeclareTColorBox
    expander3 = Expander()
    text3 = r"""
\DeclareTColorBox{mytotalbox}{O{}mO{-2mm}}{colback=red!5!white,
colframe=red!75!black,fonttitle=\bfseries,
colbacktitle=red!85!black,enhanced,
attach boxed title to top center={yshift=#3},
title=#2,#1}

\begin{mytotalbox}{My Title}
Content here.
\end{mytotalbox}
""".strip()
    out3 = expander3.expand(text3)
    out_str3 = expander3.convert_tokens_to_str(out3).strip()
    print("DeclareTColorBox test:")
    print(out_str3)
