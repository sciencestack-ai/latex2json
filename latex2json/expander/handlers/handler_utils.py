from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Handler
from latex2json.tokens.types import CommandWithArgsToken, Token, TokenType


def make_generic_command_handler(command_name: str, arg_spec: str) -> Handler:
    def generic_command_handler(expander: ExpanderCore, token: Token) -> list:
        r"""
        Generic handler for LaTeX commands based on their argument specification.
        Spec can contain:
        - * : star (asterisk)
        - [ : optional bracket argument
        - { : required brace argument
        - = : required equals sign
        - \ : required backslash
        - f : parse float
        - d : parse dimension
        - i : parse integer
        """
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
            elif char == "f":
                expander.parse_float()
            elif char == "d":
                expander.parse_dimensions()
            elif char == "i":
                expander.parse_integer()
            elif char == "=":
                eq = expander.parse_equals()
                if not eq:
                    expander.logger.warning(
                        f"Required = not found for command {command_name}"
                    )
                    break
            elif char == "\\":
                tok = expander.peek()
                if not tok or tok.type != TokenType.CONTROL_SEQUENCE:
                    expander.logger.warning(
                        f"Required \\ not found for command {command_name}"
                    )
                    break
                expander.consume()
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
                    break
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
