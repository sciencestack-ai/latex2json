"""Shared utilities for environment handlers."""

from dataclasses import dataclass
from typing import Optional, List, TYPE_CHECKING
from latex2json.latex_maps.environments import EnvironmentDefinition
from latex2json.tokens.types import (
    CommandWithArgsToken,
    EnvironmentStartToken,
    EnvironmentEndToken,
    EnvironmentType,
    Token,
    TokenType,
)
from latex2json.tokens.utils import (
    is_begin_group_token,
    is_newline_token,
    segment_tokens_by_begin_end_and_braces,
    strip_whitespace_tokens,
)

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.state import ProcessingMode


def is_nonumber_token(tok: Token) -> bool:
    return tok.type == TokenType.CONTROL_SEQUENCE and tok.value in [
        "nonumber",
        "notag",
    ]


@dataclass
class TagExtractionResult:
    notag: bool  # explicit \notag or \nonumber
    tag: Optional[str]
    tokens: List[Token]


def extract_tag_from_tokens(tokens: List[Token]) -> TagExtractionResult:
    notag: bool = False
    numbering: Optional[str] = None
    newblock: List[Token] = []
    for tok in tokens:
        if is_nonumber_token(tok):
            notag = True
        elif isinstance(tok, CommandWithArgsToken) and tok.value == "tag":
            notag = False
            numbering = tok.numbering
        else:
            newblock.append(tok)
    return TagExtractionResult(notag=notag, tag=numbering, tokens=newblock)


def create_environment_start_token(
    expander: ExpanderCore,
    env_name: str,
) -> EnvironmentStartToken:
    """Create an environment start token with proper metadata.

    Args:
        expander: The expander instance
        env_name: Name of the environment

    Returns:
        EnvironmentStartToken with display name, numbering, and type set
    """
    env_def = expander.get_environment_definition(env_name)

    display_name = env_name
    env_type = EnvironmentType.DEFAULT
    counter_name = None

    if env_def:
        display_name = env_def.display_name
        env_type = env_def.env_type
        counter_name = env_def.counter_name

    numbering = None
    if counter_name and expander.has_counter(counter_name):
        numbering = expander.get_counter_display(counter_name)

    return EnvironmentStartToken(
        env_name,
        display_name=display_name,
        numbering=numbering,
        env_type=env_type,
    )


def create_environment_end_token(
    env_name: str,
) -> EnvironmentEndToken:
    """Create an environment end token.

    Args:
        env_name: Name of the environment

    Returns:
        EnvironmentEndToken
    """
    return EnvironmentEndToken(env_name)


def process_environment_begin(
    expander: ExpanderCore,
    token: Token,
    env_name: str,
    env_def: EnvironmentDefinition,
    expand_begin_definition: bool = True,
) -> List[Token]:
    """Process environment begin logic - shared between \\begin and \\@float.

    This function contains the complete environment handling logic including:
    - Counter stepping
    - Mode pushing (for math environments)
    - Argument parsing
    - begin_definition expansion (optional)
    - EnvironmentStartToken creation
    - Hook execution
    - Special handling for verbatim/align/math environments

    Args:
        expander: The expander instance
        token: The token that triggered this (for position tracking)
        env_name: The environment name as it appears in \\begin{name}
        env_def: The environment definition
        expand_begin_definition: If True, expand the begin_definition tokens.
                                 Set to False for \\@float to avoid infinite recursion.

    Returns:
        List of tokens to insert
    """
    state = expander.state
    out_env_name = env_def.name
    counter_name = env_def.counter_name

    # Determine environment type
    is_math = env_def.env_type in [
        EnvironmentType.EQUATION,
        EnvironmentType.EQUATION_ALIGN,
    ]
    is_align = env_def.env_type == EnvironmentType.EQUATION_ALIGN
    is_verbatim = env_def.env_type == EnvironmentType.VERBATIM

    # Step counter if environment has one
    if counter_name:
        state.step_counter(counter_name)

    # Push math mode if needed
    if is_math:
        state.push_mode(ProcessingMode.MATH_DISPLAY)

    # Determine direct command (e.g., \\@float vs \\begin)
    direct_command = None
    if token.value != "begin":
        direct_command = token.value

    # Parse arguments
    args = expander.get_parsed_args(
        env_def.num_args,
        env_def.default_arg,
        force_braces_for_req_args=True,
        command_name=direct_command or f"\\begin{{{env_name}}}",
    )

    # Expand begin_definition if requested
    if expand_begin_definition:
        subbed = expander.substitute_token_args(env_def.begin_definition, args or [])
        expander.push_tokens(subbed)

    # Evaluate counter post begin definition expansion
    numbering = None
    if counter_name:
        numbering = expander.get_counter_display(counter_name)

    # Prepare token args (skip default/optional args)
    default_skip = 1 if env_def.default_arg is not None else 0
    token_args = (args or [])[default_skip:]

    # Create environment start token
    begin_token = EnvironmentStartToken(
        out_env_name,
        display_name=env_def.display_name,
        numbering=numbering,
        env_type=env_def.env_type,
        args=token_args,
        direct_command=direct_command,
    )
    begin_token.position = token.position

    out_tokens: List[Token] = [begin_token]

    # Execute hooks
    for hook in env_def.hooks.begin:
        out_tokens.extend(hook())

    # Special handling for verbatim/align/math environments
    if is_verbatim or is_align or is_math:
        # Define predicate to find matching \\end
        def is_end_env_token(token: Token) -> bool:
            r"""check for \\end"""
            is_ctrl_seq = token.type == TokenType.CONTROL_SEQUENCE
            if not is_ctrl_seq:
                return False

            # direct end_command e.g. \\endpicture
            if env_def.end_command and token.value == env_def.end_command:
                return True

            # regular \\end{...}
            if token.value == "end":
                # parse {...} after \\end to get the env name
                tokens_to_return = expander.parse_tokens_until(
                    is_begin_group_token, verbatim=True
                )
                # check {...} is the env name
                parsed_env_name = expander.parse_brace_name()
                if not parsed_env_name:
                    expander.push_tokens(tokens_to_return)
                    return False
                is_end_env_name = parsed_env_name == env_name

                # push {...} of \\end{...} back to stream
                tokens_to_return += expander.convert_str_to_tokens(
                    "{" + parsed_env_name + "}"
                )
                expander.push_tokens(tokens_to_return)
                return is_end_env_name
            return False

        if is_verbatim:
            # parse raw, verbatim
            body_block = expander.parse_tokens_until(is_end_env_token, verbatim=True)
            out_tokens.extend(body_block)
        elif is_align:
            # align environments: parse body block for \\\\ and number accordingly
            body_block = expander.expand_until(
                stop_token_logic=is_end_env_token, consume_stop_token=False
            )
            # segment into \\begin...\\end blocks
            segments = segment_tokens_by_begin_end_and_braces(body_block)
            split_body_block: List[List[Token]] = [[]]

            # split into \\\\ or \\begin...\\end
            for segment in segments:
                if not segment.tokens:
                    continue
                if segment.is_group:
                    split_body_block[-1].extend(segment.tokens)
                else:
                    for token in segment.tokens:
                        if is_newline_token(token):
                            split_body_block.append([])
                        else:
                            split_body_block[-1].append(token)

            is_numbered = env_name.isalpha()  # False if there is *

            equation_tokens = []
            for block in split_body_block:
                is_auto_numbered = is_numbered
                numbering = None

                # check for \\nonumber
                eq_result = extract_tag_from_tokens(block)
                if eq_result.notag:
                    is_auto_numbered = False
                if eq_result.tag:
                    numbering = eq_result.tag
                    is_auto_numbered = False
                newblock = strip_whitespace_tokens(eq_result.tokens)

                if is_auto_numbered:
                    state.step_counter("equation")
                    numbering = expander.get_counter_display("equation")
                # add an env start token of Equation
                equation_tokens.append(
                    EnvironmentStartToken(
                        "equation",
                        numbering=numbering,
                        env_type=EnvironmentType.EQUATION,
                    )
                )
                equation_tokens.extend(newblock)
                # add an env end token of Equation
                equation_tokens.append(EnvironmentEndToken("equation"))

            out_tokens.extend(equation_tokens)
        else:
            # typical math block
            body_block = expander.expand_until(
                stop_token_logic=is_end_env_token, consume_stop_token=False
            )
            newblock = []
            is_auto_numbered = True
            eq_result = extract_tag_from_tokens(body_block)
            if eq_result.notag:
                numbering = None
                is_auto_numbered = False
            if eq_result.tag:
                numbering = eq_result.tag
                is_auto_numbered = False
            body_block = eq_result.tokens

            if not is_auto_numbered:
                # undo step_counter with -1
                if counter_name:
                    state.add_to_counter(counter_name, -1)
            begin_token.numbering = numbering

            out_tokens.extend(body_block)

    return out_tokens


def process_environment_end(
    expander: ExpanderCore,
    token: Token,
    env_name: str,
    env_def: EnvironmentDefinition,
    expand_end_definition: bool = True,
) -> List[Token]:
    """Process environment end logic - shared between \\end and \\end@float.

    This function contains the complete environment end handling logic including:
    - end_definition expansion (optional)
    - End hook execution
    - Mode popping (for math environments)
    - EnvironmentEndToken creation

    Args:
        expander: The expander instance
        token: The token that triggered this (for direct_command tracking)
        env_name: The environment name (input name, e.g., "wrapfigure")
        env_def: The environment definition
        expand_end_definition: If True, expand the end_definition tokens.
                              Set to False for \\end@float if needed.

    Returns:
        List of tokens to insert
    """
    state = expander.state
    out_env_name = env_def.name

    # Determine environment type
    is_math = env_def.env_type in [
        EnvironmentType.EQUATION,
        EnvironmentType.EQUATION_ALIGN,
    ]

    # Determine direct command
    direct_command = None
    if token.value != "end":
        direct_command = token.value

    # Create end token
    end_token = EnvironmentEndToken(out_env_name, direct_command=direct_command)

    # Expand end_definition if requested
    if expand_end_definition:
        subbed = expander.substitute_token_args(env_def.end_definition, [])
        out_tokens = expander.expand_tokens(subbed)
    else:
        out_tokens = []

    # Execute end hooks
    for hook in env_def.hooks.end:
        out_tokens.extend(hook())

    # Pop math mode if needed
    if is_math:
        state.pop_mode()

    return out_tokens + [end_token]


def begin_environment_handler(
    expander: ExpanderCore, token: Token, check_env_handler: bool = True
) -> Optional[List[Token]]:
    r"""Shared handler for begin-like commands (\begin, \@float, \@dblfloat).

    Args:
        expander: The expander instance
        token: The token that triggered this handler
        check_env_handler: If True, check for and call env_def.begin_handler.
                          Set to False for @float/@dblfloat to use process_environment_begin directly.

    Returns:
        List of tokens to insert, or None on error
    """
    name = expander.parse_brace_name()
    if name is None:
        expander.logger.warning(
            f"{token.value} expects an environment name, but found {expander.peek()}"
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
        begin_token = create_environment_start_token(expander, name)
        return [begin_token]

    if check_env_handler and env_def.begin_handler:
        # Call the registered begin_handler (which may expand begin_definition)
        return env_def.begin_handler(expander, token)
    elif not check_env_handler:
        # For \\@float: use shared logic but skip begin_definition expansion
        return process_environment_begin(
            expander, token, name, env_def, expand_begin_definition=False
        )
    else:
        # env is defined but has no begin handler - fallback
        expander.logger.info(
            f"{token.value}{{{name}}} has no begin handler, returning default env"
        )
        begin_token = create_environment_start_token(expander, name)
        return [begin_token]


def end_environment_handler(
    expander: ExpanderCore, token: Token
) -> Optional[List[Token]]:
    r"""Shared handler for end-like commands (\end, \end@float, \end@dblfloat).

    Args:
        expander: The expander instance
        token: The token that triggered this handler

    Returns:
        List of tokens to insert, or None on error
    """
    name = expander.parse_brace_name()
    if name is None:
        expander.logger.warning(
            f"{token.value} expects an environment name, but found {expander.peek()}"
        )
        return None

    env_def = expander.state.get_environment_definition(name)

    out_tokens = [create_environment_end_token(name)]

    if not env_def:
        expander.logger.info(
            f"{token.value}{{{name}}} not found, returning default environment end token"
        )
    elif env_def.end_handler:
        out_tokens = env_def.end_handler(expander, token)
    else:
        # env is defined but has no end handler
        expander.logger.info(
            f"{token.value}{{{name}}} has no end handler, returning default environment end token"
        )

    # pop scope at the end!
    expander.pop_env_stack(name)
    expander.pop_scope()

    return out_tokens
