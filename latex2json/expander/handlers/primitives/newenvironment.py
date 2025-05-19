from dataclasses import dataclass
from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.primitives.newcommand import (
    get_newcommand_args_and_definition,
    get_parsed_args_from_newcommand,
)
from latex2json.expander.handlers.utils import substitute_token_args
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import is_begin_bracket_token, is_begin_group_token


@dataclass
class NewEnvironmentResult:
    name: str
    begin_definition: List[Token]
    end_definition: List[Token]
    num_args: int
    default_arg: Optional[List[Token]] = None


class NewEnvironmentMacro(Macro):
    def __init__(self, name: str, allow_redefine: bool = False):
        super().__init__(name)
        self.allow_redefine = allow_redefine
        self.handler = lambda expander, node: self._expand(expander, node)

    def _expand(self, expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        out = newenvironment_handler(expander, token, self.allow_redefine)
        if out is None:
            return None

        begin_name = "\\" + out.name
        end_name = "\\end" + out.name

        def begin_handler(
            expander: ExpanderCore, token: Token
        ) -> Optional[List[Token]]:
            args = get_parsed_args_from_newcommand(
                expander, out.num_args, out.default_arg
            )
            if args is None:
                return None

            subbed = substitute_token_args(out.begin_definition, args, math_mode=False)
            expander.stream.push_tokens(subbed)
            return []

        def end_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
            subbed = substitute_token_args(out.end_definition, [], math_mode=False)
            expander.stream.push_tokens(subbed)
            return []

        # Register both \begin{name} and \end{name} macros
        begin_macro = Macro(begin_name, begin_handler, out.begin_definition)
        end_macro = Macro(end_name, end_handler, out.end_definition)

        expander.register_macro(begin_name, begin_macro, is_global=True)
        expander.register_macro(end_name, end_macro, is_global=True)

        return []


def newenvironment_handler(
    expander: ExpanderCore, token: Token, allow_redefine: bool = False
) -> Optional[NewEnvironmentResult]:
    expander.parse_asterisk()
    name = expander.parse_environment_name()
    if name is None:
        expander.logger.warning(
            f"Warning: \\newenvironment expects an environment name, but found {token}"
        )
        return None

    # Check if environment already exists
    if not allow_redefine and (
        expander.state.get_macro("\\" + name)
        or expander.state.get_macro("\\end" + name)
    ):
        expander.logger.warning(
            f"Warning: environment {name} already exists. Use \\renewenvironment to redefine"
        )
        return None

    parsed = get_newcommand_args_and_definition(expander)
    if parsed is None:
        return None

    num_args, default_arg, begin_definition = parsed

    # Parse end definition
    expander.skip_whitespace()
    end_definition = expander.parse_brace_as_tokens()
    if end_definition is None:
        expander.logger.warning(
            f"Warning: \\newenvironment expects an end definition in braces"
        )
        return None

    return NewEnvironmentResult(
        name=name,
        begin_definition=begin_definition,
        end_definition=end_definition,
        num_args=num_args,
        default_arg=default_arg,
    )


def register_newenvironment(expander: ExpanderCore):
    expander.register_macro(
        "\\newenvironment",
        NewEnvironmentMacro("\\newenvironment", allow_redefine=False),
        is_global=True,
    )
    expander.register_macro(
        "\\renewenvironment",
        NewEnvironmentMacro("\\renewenvironment", allow_redefine=True),
        is_global=True,
    )


if __name__ == "__main__":
    expander = ExpanderCore()
    register_newenvironment(expander)

    # Basic environment
    expander.expand(r"\newenvironment{test}{Begin test}{End test}")
    print(expander.expand(r"\begin{test}Content\end{test}"))

    # Environment with arguments
    expander.expand(r"\newenvironment{boxed}[1]{#1: \begin{box}}{\\end{box}}")
    print(expander.expand(r"\begin{boxed}{Title}Content\end{boxed}"))

    # Environment with default argument
    expander.expand(r"\newenvironment{note}[1][Note]{{\bf #1:}}{}")
    print(expander.expand(r"\begin{note}Content\end{note}"))
