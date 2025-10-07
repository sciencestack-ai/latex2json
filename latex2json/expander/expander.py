from logging import Logger
from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.latex_maps.environments import EnvironmentDefinition
from latex2json.latex_maps.whitelist import (
    WHITELISTED_COMMANDS,
    WHITELISTED_ENVIRONMENTS,
    WHITELISTED_PACKAGES,
    WHITELISTED_CLASSES,
)
from latex2json.tokens.tokenizer import Tokenizer
from latex2json.tokens.types import Token


class Expander(ExpanderCore):
    def __init__(
        self,
        tokenizer: Optional[Tokenizer] = None,
        logger: Optional[Logger] = None,
        prevent_whitelisted_redefinitions: bool = True,
        prevent_package_macro_execution: bool = False,
    ):
        self.prevent_package_macro_execution = prevent_package_macro_execution
        self.prevent_whitelisted_redefinitions = prevent_whitelisted_redefinitions
        super().__init__(tokenizer, logger)

        self.white_listed_commands: List[str] = WHITELISTED_COMMANDS.copy()
        self.white_listed_environments: List[str] = WHITELISTED_ENVIRONMENTS.copy()
        self.white_listed_classes: List[str] = WHITELISTED_CLASSES.copy()
        self.white_listed_packages: List[str] = WHITELISTED_PACKAGES.copy()

        self._register_handlers_and_packages()

    def _register_handlers_and_packages(self):
        from latex2json.expander.handlers import register_handlers
        from latex2json.expander.packages import register_packages

        register_handlers(self)
        register_packages(self)

    # override
    def load_package(self, package_name: str, extension: str = ".sty", read_file=True):
        if package_name in self.white_listed_packages:
            return None
        return super().load_package(package_name, extension, read_file)

    # override
    def load_class(self, class_name: str, extension: str = ".cls", read_file=True):
        if class_name in self.white_listed_classes:
            return None
        return super().load_class(class_name, extension, read_file)

    # override
    def _exec_macro(self, tok: Token) -> List[Token] | None:
        if self.state.in_package_or_class and self.prevent_package_macro_execution:
            return [tok]
        return super()._exec_macro(tok)

    # override
    def register_environment(
        self,
        env_name: str,
        env_def: EnvironmentDefinition,
        is_global: bool = True,
        is_user_defined: bool = False,
    ) -> None:
        if is_user_defined and self.prevent_whitelisted_redefinitions:
            if env_name in self.white_listed_environments:
                self.logger.info(
                    f"Preventing redefinition of white-listed environment {env_name}"
                )
                return
        return super().register_environment(
            env_name, env_def, is_global, is_user_defined
        )

    # override
    def register_macro(
        self,
        tok_or_name: str | Token,
        macro: Macro,
        is_global: bool = False,
        is_user_defined: bool = False,
    ):
        normalized = self.normalize_macro_name(tok_or_name)
        if normalized is None:
            return  # Invalid token type, cannot register
        tok_str, is_active_char = normalized

        # prevent redefinition of white-listed commands in package/class files
        if is_user_defined and self.prevent_whitelisted_redefinitions:
            if not is_active_char:
                tok_str = tok_str.lstrip("\\")
            if tok_str in self.white_listed_commands:
                self.logger.info(
                    f"Preventing redefinition of white-listed command \\{tok_str}"  # inside package/class: \\{name}"
                )
                return

        super().register_macro(tok_or_name, macro, is_global, is_user_defined)


if __name__ == "__main__":
    from latex2json.tokens.utils import is_whitespace_token, strip_whitespace_tokens

    expander = Expander(prevent_whitelisted_redefinitions=False)
    text = r"""
\renewenvironment{abstract}%
{%
  \begin{quote}
}
{
  \end{quote}%
}

\begin{abstract}
ABSTRACT
\end{abstract}
"""
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)

    # while not expander.eof():
    #     next_tokens = expander.next_non_expandable_tokens()
    #     if not next_tokens:
    #         break
    #     stripped = strip_whitespace_tokens(next_tokens)
    #     if stripped:
    #         print(stripped)
