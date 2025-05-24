import enum
import dataclasses
from typing import List, Optional, Dict, Any, Tuple, Callable, Union

from latex2json.expander.macro_registry import Macro, MacroRegistry
from latex2json.expander.registers import RegisterType, TexRegisters
from latex2json.tokens import Catcode, get_default_catcodes
from latex2json.tokens.tokenizer import Tokenizer


class ProcessingMode(enum.Enum):
    TEXT = 1
    MATH = 2
    # ... other modes


class StateLayer:
    """Represents the state for a single scope layer."""

    def __init__(self, parent: Optional["StateLayer"] = None):
        self._parent = parent

        # --- State that might not be strictly layered but is part of the scope ---
        # Mode: Often copied, but changes are local
        self.mode: ProcessingMode = parent.mode if parent else ProcessingMode.TEXT

        # --- Scoped State ---
        # Macro Registry: Layered lookup
        self.macro_registry = MacroRegistry(
            parent=parent.macro_registry if parent else None
        )

        # Catcode Table: Copied, local changes don't affect parent
        # Use a copy of the parent's table, or a default if no parent
        self.catcode_table: Dict[int, Catcode] = (
            parent.catcode_table.copy() if parent else get_default_catcodes()
        )

        self.register_old_values: List[Tuple[str, Union[int, str], Any]] = []

    def get_catcode(self, char_ord: int) -> Catcode:
        """Get the catcode for a character from this layer's table."""
        return self.catcode_table.get(
            char_ord, Catcode.OTHER
        )  # Default to OTHER if not found

    def set_catcode(self, char_ord: int, catcode: Catcode):
        """Set the catcode for a character in this layer's table."""
        self.catcode_table[char_ord] = catcode

    def get_macro(self, name: str) -> Optional[Macro]:
        return self.macro_registry.get(name)

    def set_macro(self, name: str, definition: Macro, is_global: bool = False):
        self.macro_registry.set(name, definition, is_global)

    # # --- Methods to access/modify state within this layer ---

    # Add methods for getting/setting other state (registers, parameters, mode, etc.)
    # These methods would interact with self.local_register_assignments, self.parameter_values, etc.
    # and potentially delegate to parent layers or a global store for non-local state.


# --- ExpanderState Class (The Stack Manager) ---


class ExpanderState:
    """Manages the stack of StateLayer objects."""

    def __init__(self, tokenizer: Tokenizer):
        # Initialize with the base global state layer
        self._stack: List[StateLayer] = [StateLayer()]
        self.tokenizer = tokenizer
        self.pending_global = False

        self.registers = TexRegisters()

    @property
    def mode(self) -> ProcessingMode:
        return self.current.mode

    def get_register(self, name: str, reg_id: Union[int, str]) -> Any:
        return self.registers.get_register(name, reg_id)

    def set_register(
        self,
        register_type: RegisterType,
        reg_id: Union[int, str],
        value: Any,
        is_global: bool = False,
    ):
        is_global = self.pending_global or is_global
        if not is_global:
            cur_value = self.registers.get_register(
                register_type, reg_id
            )  # could be None
            # store changes
            self.current.register_old_values.append((register_type, reg_id, cur_value))
        self.registers.set_register(register_type, reg_id, value)
        self.pending_global = False

    def get_root(self) -> StateLayer:
        """Get the root state layer (the first layer in the stack)."""
        return self._stack[0]

    @property
    def current(self) -> StateLayer:
        """Get the currently active state layer (top of the stack)."""
        if not self._stack:
            raise RuntimeError("ExpanderState stack is empty!")
        return self._stack[-1]

    def push_scope(self):
        """Pushes a new state layer onto the stack, starting a new scope."""
        # Create a new layer, inheriting from the current layer
        new_layer = StateLayer(parent=self.current)
        self._stack.append(new_layer)
        self.tokenizer.set_catcode_table(self.current.catcode_table)

    def pop_scope(self):
        """Pops the current state layer from the stack, ending the current scope."""
        if len(self._stack) <= 1:
            # Cannot pop the base global scope
            print("[WARNING]: Cannot pop the base ExpanderState scope!")
            return
        last_state = self._stack.pop()
        self.tokenizer.set_catcode_table(self.current.catcode_table)
        # setback the old values
        for change in reversed(last_state.register_old_values):
            name, reg_id, value = change
            if value is None:
                self.registers.delete_register(name, reg_id)
            else:
                self.registers.set_register(name, reg_id, value)

    def get_macro(self, name: str) -> Optional[Macro]:
        return self.current.get_macro(name)

    def get_all_macros(self) -> Dict[str, Macro]:
        return self.current.macro_registry.get_all_macros()

    def set_macro(self, name: str, definition: Macro, is_global: bool = False):
        self.current.set_macro(name, definition, is_global or self.pending_global)
        self.pending_global = False

    def set_catcode(self, char_ord: int, catcode: Catcode):
        """Set the catcode for a character in the current scope."""
        self.current.set_catcode(char_ord, catcode)
        self.tokenizer.set_catcode(char_ord, catcode)

    def get_catcode(self, char_ord: int) -> Catcode:
        """Get the current catcode for a character."""
        return self.current.get_catcode(char_ord)

    def set_mode(self, mode: ProcessingMode):
        """Set the mode for the current scope."""
        self.current.mode = mode
