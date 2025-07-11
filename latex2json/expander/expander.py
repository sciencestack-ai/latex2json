from logging import Logger
from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.latex_maps.environments import EnvironmentDefinition
from latex2json.latex_maps.whitelist import (
    WHITELISTED_COMMANDS,
    WHITELISTED_ENVIRONMENTS,
)
from latex2json.tokens.tokenizer import Tokenizer


class Expander(ExpanderCore):
    def __init__(
        self,
        tokenizer: Optional[Tokenizer] = None,
        logger: Optional[Logger] = None,
    ):
        super().__init__(tokenizer, logger)

        self._register_handlers_and_packages()

        self.white_listed_commands: List[str] = WHITELISTED_COMMANDS.copy()
        self.white_listed_environments: List[str] = WHITELISTED_ENVIRONMENTS.copy()
        self.white_listed_classes: List[str] = ["subfiles"]
        self.white_listed_packages: List[str] = ["subfiles"]

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
    def register_environment(
        self,
        env_name: str,
        env_def: EnvironmentDefinition,
        is_global: bool = True,
        is_user_defined: bool = False,
    ) -> None:
        if is_user_defined:
            if env_name in self.white_listed_environments:
                self.logger.warning(
                    f"Preventing redefinition of white-listed environment {env_name}"
                )
                return
        return super().register_environment(
            env_name, env_def, is_global, is_user_defined
        )

    # override
    def register_macro(
        self,
        name: str,
        macro: Macro,
        is_global: bool = False,
        is_user_defined: bool = False,
    ):
        # prevent redefinition of white-listed commands in package/class files
        if is_user_defined:
            if name in self.white_listed_commands:
                self.logger.warning(
                    f"Preventing redefinition of white-listed command \\{name}"  # inside package/class: \\{name}"
                )
                return

        super().register_macro(name, macro, is_global, is_user_defined)


if __name__ == "__main__":
    expander = Expander()
    from latex2json.tokens.utils import is_whitespace_token, strip_whitespace_tokens

    text = r"""\numexpr 1+1\relax"""

    expander.set_text(text)
    # out = expander.expand(text)

    # while not expander.eof():
    #     next_tokens = expander.next_non_expandable_tokens()
    #     if not next_tokens:
    #         break
    #     stripped = strip_whitespace_tokens(next_tokens)
    #     if stripped:
    #         print(stripped)
