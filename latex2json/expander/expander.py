from logging import Logger
from typing import Callable, List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Handler, Macro
from latex2json.latex_maps.environments import EnvironmentDefinition
from latex2json.latex_maps.whitelist import (
    STRICTLY_BLOCKED_COMMANDS,
    PROTECTED_COMMANDS,
    WHITELISTED_ENVIRONMENTS,
    WHITELISTED_PACKAGES,
    WHITELISTED_CLASSES,
)
from latex2json.tokens.tokenizer import Tokenizer
from latex2json.tokens.types import CommandWithArgsToken, Token

StorageCallback = Callable[["ExpanderCore", List[List[Token]]], None]
ReturnCallback = Callable[["ExpanderCore", List[List[Token]], List[Token]], List[Token]]


def create_wrapped_protected_handler(
    command_name: str,
    macro: Macro,
    storage_callback: Optional[StorageCallback] = None,
    return_callback: Optional[ReturnCallback] = None,
) -> Handler:
    r"""
    Create a wrapped handler for user-redefined protected commands.

    The wrapper:
    1. Parses arguments according to user's signature
    2. Executes the user's definition (side effects happen)
    3. Optionally stores args via storage_callback
    4. Returns result from return_callback or empty list

    Args:
        command_name: Name of the command (e.g., "title", "abstract", "@title")
        macro: The user-defined macro
        storage_callback: Optional function to store parsed args (e.g., in frontmatter)
        return_callback: Optional function(exp, args, expanded_output) to generate return tokens

    Example:
        # For \title - store args
        def store(exp, args):
            exp.state.frontmatter["title"] = args
        handler = create_wrapped_protected_handler("title", macro, storage_callback=store)

        # For \@title - return semantic token with expanded output
        def return_semantic(exp, args, output):
            return [CommandWithArgsToken("title", args=[output])]
        handler = create_wrapped_protected_handler("@title", macro, return_callback=return_semantic)
    """
    num_args = macro.num_args
    default_arg = macro.default_arg
    original_definition = macro.definition.copy()

    def handler(exp: "ExpanderCore", tok: Token) -> List[Token]:
        # Parse args according to user's signature
        args = exp.get_parsed_args(
            num_args=num_args, default_arg=default_arg, command_name=tok.value
        )
        if args is None:
            args = []

        # Execute user's definition (side effects like \newcommand)
        definition_with_args = exp.substitute_token_args(original_definition, args)
        expanded_output = exp.expand_tokens(definition_with_args)

        # Store args if callback provided
        if storage_callback:
            storage_callback(exp, args)

        # Return result from callback or empty
        if return_callback:
            # Pass both args (for metadata) and expanded output (actual content)
            return return_callback(exp, args, expanded_output)
        return []

    return handler


class Expander(ExpanderCore):
    def __init__(
        self,
        tokenizer: Optional[Tokenizer] = None,
        logger: Optional[Logger] = None,
        strictly_blocked_commands: Optional[List[str]] = STRICTLY_BLOCKED_COMMANDS,
        protected_commands: Optional[List[str]] = PROTECTED_COMMANDS,
        whitelisted_environments: Optional[List[str]] = WHITELISTED_ENVIRONMENTS,
        ignore_package_cls: bool = False,
    ):
        self.ignore_package_cls = ignore_package_cls
        super().__init__(tokenizer, logger)

        # Commands that BLOCK redefinition entirely (strict blocking - never allow)
        self.strictly_blocked_commands: List[str] = (
            strictly_blocked_commands.copy()
            if strictly_blocked_commands is not None
            else []
        )
        self.white_listed_environments: List[str] = (
            whitelisted_environments.copy()
            if whitelisted_environments is not None
            else []
        )
        self.white_listed_classes: List[str] = WHITELISTED_CLASSES.copy()
        self.white_listed_packages: List[str] = WHITELISTED_PACKAGES.copy()

        # Initialize protected_commands early (before handlers)
        # Will be populated with frontmatter keys after handler registration
        base_protected = (
            protected_commands if protected_commands is not None else PROTECTED_COMMANDS
        )
        self.protected_commands: set[str] = set(base_protected)

        self._register_handlers_and_packages()

        # Add frontmatter commands to protected set (now that handlers are registered)
        self.protected_commands.update(self.state.frontmatter.keys())
        self.protected_commands.update([f"@{k}" for k in self.state.frontmatter.keys()])
        self.protected_commands.add("@maketitle")

    def _register_handlers_and_packages(self):
        from latex2json.expander.handlers import register_handlers
        from latex2json.expander.packages import register_packages

        register_handlers(self)
        register_packages(self)

    # override
    def load_package(
        self, package_name: str, read_file=True, extension: Optional[str] = ".sty"
    ):
        if self.ignore_package_cls:
            return None
        if package_name in self.white_listed_packages:
            return None
        return super().load_package(
            package_name, read_file=read_file, extension=extension
        )

    # override
    def load_class(
        self, class_name: str, read_file=True, extension: Optional[str] = ".cls"
    ):
        if self.ignore_package_cls:
            return None
        if class_name in self.white_listed_classes:
            return None
        return super().load_class(class_name, read_file=read_file, extension=extension)

    # # override
    # def _exec_macro(self, tok: Token) -> List[Token] | None:
    #     if self.state.in_package_or_class and self.prevent_package_macro_execution:
    #         return [tok]
    #     return super()._exec_macro(tok)

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

        # Prevent redefinition of strictly blocked commands
        if is_user_defined:
            if not is_active_char:
                tok_str = tok_str.lstrip("\\")
            if tok_str in self.strictly_blocked_commands:
                self.logger.info(
                    f"Preventing redefinition of strictly blocked command \\{tok_str}"
                )
                return

            # Apply protection wrapping for protected commands
            cmd_name = tok_str.lstrip("\\")
            if cmd_name in self.protected_commands:
                # Determine callbacks based on command type
                storage_callback = None
                return_callback = None

                # # Frontmatter storage commands (\title, \author, etc.)
                # if cmd_name in self.state.frontmatter:
                #     storage_callback = (
                #         lambda exp, args: exp.state.frontmatter.__setitem__(
                #             cmd_name, args
                #         )
                #     )

                # Frontmatter accessor commands (\@title, \@author, etc.)
                if cmd_name.startswith("@") and cmd_name[1:] in self.state.frontmatter:
                    key = cmd_name[1:]
                    return_callback = lambda exp, args, output: [
                        CommandWithArgsToken(key, args=[output])
                    ]

                # \@maketitle - special semantic wrapper
                elif cmd_name == "@maketitle":
                    return_callback = lambda exp, args, output: [
                        CommandWithArgsToken("maketitle", args=[output])
                    ]

                else:
                    # Generic protected commands - return semantic token with expanded args
                    # e.g. \def\xxx{XXX} \abstract{\xxx} -> CommandWithArgsToken("abstract", args=["XXX"])

                    def make_return_callback(name):
                        def callback(exp: ExpanderCore, args: List[Token], output):
                            expanded_args = [exp.expand_tokens(arg) for arg in args]
                            return [CommandWithArgsToken(name, args=expanded_args)]

                        return callback

                    return_callback = make_return_callback(cmd_name)

                # Create wrapped handler
                macro.handler = create_wrapped_protected_handler(
                    cmd_name, macro, storage_callback, return_callback
                )

        super().register_macro(tok_or_name, macro, is_global, is_user_defined)


if __name__ == "__main__":
    from latex2json.tokens.utils import is_whitespace_token, strip_whitespace_tokens

    expander = Expander()
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
