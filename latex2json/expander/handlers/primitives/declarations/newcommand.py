from dataclasses import dataclass
from typing import List, Optional, Tuple
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.primitives.declarations.declaration_utils import (
    get_newcommand_args_and_definition,
)
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import Token


@dataclass
class NewCommandResult:
    name: str
    definition: List[Token]
    num_args: int
    default_arg: Optional[List[Token]] = None


class NewCommandMacro(Macro):
    def __init__(self, name: str, allow_redefine: bool = False):
        super().__init__(name)
        self.allow_redefine = allow_redefine
        self.handler = lambda expander, node: self._expand(expander, node)

    def _expand(self, expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        out = newcommand_handler(expander, token, self.allow_redefine)
        if out is None:
            return None

        def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
            # Parse exactly num_args arguments
            args = expander.get_parsed_args(
                out.num_args, out.default_arg, command_name=self.name
            )
            if args is None:
                return None

            subbed = expander.substitute_token_args(out.definition, args)
            expander.push_tokens(subbed)
            return []

        macro = Macro(out.name, handler, out.definition)
        expander.register_macro(out.name, macro, is_global=True, is_user_defined=True)

        return []


def newcommand_handler(
    expander: ExpanderCore, token: Token, allow_redefine: bool = True
) -> Optional[NewCommandResult]:
    expander.parse_asterisk()
    name = expander.parse_command_name()
    if name is None:
        expander.logger.warning(
            f"Warning: \\newcommand expects a command name, but found {expander.peek()}"
        )
        return None

    name = name.strip()

    out = get_newcommand_args_and_definition(expander)
    if out is None:
        expander.logger.warning(
            f"Warning: \\newcommand {name} expects a definition in braces"
        )
        return None

    # Check if command already exists
    if not allow_redefine and expander.state.get_macro(name):
        expander.logger.warning(
            f"Warning: command {name} already exists. Use \\renewcommand to redefine"
        )
        return None

    num_args, default_arg, definition = out

    return NewCommandResult(
        name=name, definition=definition, num_args=num_args, default_arg=default_arg
    )


def register_newcommand(expander: ExpanderCore):
    expander.register_macro(
        "\\newcommand",
        NewCommandMacro("\\newcommand", allow_redefine=False),
        is_global=True,
    )
    expander.register_macro(
        "\\renewcommand",
        NewCommandMacro("\\renewcommand", allow_redefine=True),
        is_global=True,
    )
    expander.register_macro(
        "\\providecommand",
        NewCommandMacro("\\providecommand", allow_redefine=True),
        is_global=True,
    )


if __name__ == "__main__":
    expander = ExpanderCore()
    register_newcommand(expander)

    # # Basic command
    # expander.expand(r"\newcommand{\hello}{Hello, world!}")
    # print(expander.expand(r"\hello"))

    # # Command with arguments
    # expander.expand(r"\newcommand{\greet}[2]{Hello #1 and #2!}")
    # out = expander.expand(r"\greet{Alice}{Bob}")

    # Command with default argument
    expander.expand(r"\newcommand\welcome[1][friend]{Hello, #1!}")
    out = expander.expand(r"\welcome{Alice}")  # Uses provided argument
