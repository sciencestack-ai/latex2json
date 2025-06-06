from enum import Enum
from typing import Any, Dict, List, Callable, Optional, TYPE_CHECKING

from latex2json.tokens.types import Token

if TYPE_CHECKING:
    from latex2json.expander.expander_core import ExpanderCore


Handler = Callable[["ExpanderCore", Token], Optional[List[Token]]]


class MacroType(Enum):
    MACRO = "macro"
    CHAR = "char"
    IF = "if"
    REGISTER = "register"

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)


# Base class for command definitions (Primitives and Macros)
class Macro:
    def __init__(
        self,
        name: str,
        handler: Optional[Handler] = None,
        definition: List[Token] = [],
        type: MacroType = MacroType.MACRO,  # "macro" or "char" (e.g. \let \bgroup etc are single character tokens and treated differently for \ifx etc)
    ):
        self.name = name  # usually the command name e.g. \foo

        # handler: Controls how tokens are processed during macro expansion
        # - To have tokens continue expanding: use expander.push_tokens() in handler and return []
        # - To prevent further expansion: return the tokens directly from the handler. Example usecase: preserving braces {} so that they don't get expanded, or \meaning output the raw tokens
        # Case: see \expandafter (push tokens back to stream, return []) vs \noexpand (return [token] directly)
        self.handler = handler

        # definition: Raw tokens that define this macro's replacement text
        # These tokens will be expanded when the macro is called.
        # Useful for inspecting macro definitions ie debugging or copying macro definitions directly without expanding the stream
        self.definition = definition
        self.type = type


class MacroRegistry:
    """
    Manages macro and primitive definitions for a single scope layer.
    Uses a parent registry for lookup chaining in higher scopes.
    """

    def __init__(self, parent: Optional["MacroRegistry"] = None):
        self._definitions: Dict[str, Macro] = {}
        self._parent = parent

    @property
    def parent(self) -> Optional["MacroRegistry"]:
        return self._parent

    def set(self, name: str, definition: Macro, is_global: bool = False):
        """
        Sets a definition in this registry layer.
        If is_global is True, it propagates the definition up to the root registry.
        """
        if not name.startswith("\\"):
            name = f"\\{name}"

        if is_global and self._parent:
            # If global and has a parent, delegate to the parent's set method
            # until we reach the root registry (which has no parent).
            self._parent.set(name, definition, is_global=True)
        else:
            # Set the definition in the current layer's dictionary.
            # This definition shadows any definitions in parent layers.
            self._definitions[name] = definition

    def delete(self, name: str, is_global: bool = False):
        """
        Deletes a definition from this registry layer.
        """
        if not name.startswith("\\"):
            name = f"\\{name}"

        if is_global and self._parent:
            self._parent.delete(name, is_global=True)
        else:
            if name in self._definitions:
                del self._definitions[name]

    def get(self, name: str) -> Optional[Macro]:
        """
        Retrieves the definition for the given name, checking this layer
        and then recursively checking parent layers.
        """
        if not name.startswith("\\"):
            name = f"\\{name}"

        # Check the current layer first
        if name in self._definitions:
            return self._definitions[name]

        # If not found in the current layer, check the parent registry
        if self._parent:
            return self._parent.get(name)

        # If no parent and not found, the definition is not in scope
        return None

    def register_handler(
        self,
        name: str,
        handler: Handler,
        is_global: bool = False,
    ):
        """Convenience method to define a primitive in this registry layer (usually the root)."""
        macro_def = Macro(name, handler)
        # Primitives are typically defined globally in the root registry.
        # We use set with is_global=True to ensure it goes to the root if called on a child.
        self.set(name, macro_def, is_global=is_global)

    def get_all_macros(self) -> Dict[str, Macro]:
        """Returns all macros in this registry and its parents."""
        all_macros = {}
        current = self
        while current:
            for name, definition in current._definitions.items():
                # if definition.is_macro:
                all_macros[name] = definition
            current = current.parent
        return all_macros
