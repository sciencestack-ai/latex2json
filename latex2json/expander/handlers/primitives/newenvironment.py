from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.primitives.newcommand import (
    get_newcommand_args_and_definition,
)
from latex2json.expander.macro_registry import Macro
from latex2json.latex_maps.environments import EnvironmentDefinition
from latex2json.tokens.types import Token, TokenType


class NewEnvironmentMacro(Macro):
    def __init__(self, name: str, allow_redefine: bool = False):
        super().__init__(name)
        self.allow_redefine = allow_redefine
        self.handler = lambda expander, node: self._expand(expander, node)

    def _expand(self, expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        expander.parse_asterisk()
        name = expander.parse_environment_name()
        if name is None:
            expander.logger.warning(
                f"Warning: \\newenvironment expects an environment name, but found {token}"
            )
            return None

        # Check if environment already exists
        if not self.allow_redefine and (expander.state.get_macro("\\" + name)):
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

        env_def = EnvironmentDefinition(
            name=name,
            begin_definition=begin_definition,
            end_definition=end_definition,
            num_args=num_args,
            default_arg=default_arg,
            has_direct_command=name.isalpha(),
        )

        expander.register_environment(env_def, is_global=True)

        return []


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
