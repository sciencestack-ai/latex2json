"""
Generic wrapper system for protected commands.

Allows user redefinitions of whitelisted commands while preserving semantic behavior.
For example, \renewcommand{\abstract}[1]{...} can execute side effects while still
being wrapped for downstream processing.
"""

from typing import Callable, List, Optional, TYPE_CHECKING
from latex2json.expander.macro_registry import Handler, Macro
from latex2json.tokens.types import Token

if TYPE_CHECKING:
    from latex2json.expander.expander_core import ExpanderCore


StorageCallback = Callable[["ExpanderCore", List[List[Token]]], None]
ReturnCallback = Callable[["ExpanderCore", List[List[Token]], List[Token]], List[Token]]


def create_wrapped_protected_handler(
    command_name: str,
    macro: Macro,
    storage_callback: Optional[StorageCallback] = None,
    return_callback: Optional[ReturnCallback] = None,
) -> Handler:
    """
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
    num_args = getattr(macro, "num_args", 0)
    default_arg = getattr(macro, "default_arg", None)
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
