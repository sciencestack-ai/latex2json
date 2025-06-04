from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Handler
from latex2json.tokens.types import CommandWithArgsToken, Token


def make_generic_command_handler(command_name: str, arg_spec: str) -> Handler:
    """
    Generic handler for LaTeX commands based on their argument specification.
    Spec string can contain: * (star), [ (optional arg), { (required arg)
    Returns empty list if required arguments are not found.
    """

    def generic_command_handler(expander: ExpanderCore, token: Token) -> list:
        spec = arg_spec
        if len(spec) == 0:
            return []

        args: List[List[Token]] = []
        opt_args: List[List[Token]] = []
        has_star = False

        if spec[0] == "*":
            has_star = expander.parse_asterisk()
            spec = spec[1:]

        for char in spec:
            expander.skip_whitespace()
            if char == "*":
                expander.parse_asterisk()
            elif char == "[":
                opt_arg = expander.parse_bracket_as_tokens(expand=True)
                if opt_arg:
                    opt_args.append(opt_arg)
            elif char == "{":
                req_arg = expander.parse_brace_as_tokens(expand=True)
                if not req_arg:  # Required argument not found
                    expander.logger.warning(
                        f"Required argument not found for command {command_name}"
                    )
                    return []
                args.append(req_arg)

        return [CommandWithArgsToken(name=command_name, args=args, opt_args=opt_args)]

    return generic_command_handler


def make_N_blocks_ignore_handler(command: str, n_blocks: int) -> Handler:
    def ignore_handler(expander: ExpanderCore, token: Token) -> Optional[list[Token]]:
        blocks = expander.parse_braced_blocks(n_blocks, expand=True)
        return []

    return ignore_handler


def make_argspec_ignore_handler(command: str, argspec: str) -> Handler:
    handler = make_generic_command_handler(command, argspec)

    def ignore_handler(expander: ExpanderCore, token: Token) -> Optional[list[Token]]:
        tokens = handler(expander, token)
        return []

    return ignore_handler


def register_ignore_handlers_util(
    expander: ExpanderCore, ignore_patterns: dict[str, int | str]
):
    """Register all formatting-related command handlers"""
    for command, spec in ignore_patterns.items():
        if isinstance(spec, str):
            handler = make_argspec_ignore_handler(command, spec)
        else:
            handler = make_N_blocks_ignore_handler(command, spec)
        expander.register_handler(
            command,
            handler,
            is_global=True,
        )
