from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Handler
from latex2json.tokens.types import CommandWithArgsToken, Token, TokenType


def make_generic_command_handler(
    command_name: str, arg_spec: str, expand: bool = True
) -> Handler:
    def generic_command_handler(expander: ExpanderCore, token: Token) -> list:
        r"""
        Generic handler for LaTeX commands based on their argument specification.
        Spec can contain:
        - * : star (asterisk)
        - [ : optional bracket argument
        - { : required brace argument or immediate token
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
                # if not eq:
                #     expander.logger.warning(
                #         f"Required = not found for command {command_name}"
                #     )
                #     break
            elif char == "\\":
                tok = expander.peek()
                if not tok or tok.type != TokenType.CONTROL_SEQUENCE:
                    expander.logger.warning(
                        f"Required \\ not found for command {command_name}"
                    )
                    break
                expander.consume()
            elif char == "[":
                opt_arg = expander.parse_bracket_as_tokens(expand=expand)
                if opt_arg:
                    opt_args.append(opt_arg)
            elif char == "{":
                req_arg = expander.parse_immediate_token(expand=expand)
                if req_arg is None:  # Required argument not found
                    expander.logger.warning(
                        f"Required argument not found for command {command_name}"
                    )
                    break
                args.append(req_arg)

        return [CommandWithArgsToken(name=command_name, args=args, opt_args=opt_args)]

    return generic_command_handler


def make_N_blocks_ignore_handler(
    command: str, n_blocks: int, expand: bool = False
) -> Handler:
    def ignore_handler(expander: ExpanderCore, token: Token) -> Optional[list[Token]]:
        blocks = expander.parse_braced_blocks(n_blocks, expand=expand)
        return []

    return ignore_handler


def make_argspec_ignore_handler(
    command: str, argspec: str, expand: bool = False
) -> Handler:
    handler = make_generic_command_handler(command, argspec, expand=expand)

    def ignore_handler(expander: ExpanderCore, token: Token) -> Optional[list[Token]]:
        tokens = handler(expander, token)
        return []

    return ignore_handler


def register_ignore_handlers_util(
    expander: ExpanderCore, ignore_patterns: dict[str, int | str], expand: bool = False
):
    """Register all formatting-related command handlers"""
    for command, spec in ignore_patterns.items():
        if isinstance(spec, str):
            handler = make_argspec_ignore_handler(command, spec, expand=expand)
        else:
            handler = make_N_blocks_ignore_handler(command, spec, expand=expand)
        expander.register_handler(
            command,
            handler,
            is_global=True,
        )
