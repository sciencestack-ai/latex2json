import enum
from typing import List, Optional, Dict, Any, Tuple, Union

from latex2json.expander.macro_registry import Macro, MacroRegistry
from latex2json.latex_maps.environments import EnvironmentDefinition
from latex2json.registers import RegisterType, TexRegisters
from latex2json.registers.types import CounterFormat
from latex2json.tokens import Catcode, get_default_catcodes
from latex2json.tokens.tokenizer import Tokenizer
from latex2json.registers.counters import CounterManager


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

        self.catcode_old_values: List[Tuple[int, Catcode]] = []

        self.register_old_values: List[Tuple[str, Union[int, str], Any]] = []

    def store_catcode_old_value(self, char_ord: int, old_value: Catcode):
        """Store the old catcode value before modification."""
        self.catcode_old_values.append((char_ord, old_value))

    def get_macro(self, name: str) -> Optional[Macro]:
        return self.macro_registry.get(name)

    def set_macro(self, name: str, definition: Macro, is_global: bool = False):
        self.macro_registry.set(name, definition, is_global)

    def apply_old_values_to_state(self, state: "ExpanderState"):
        # Restore old catcode values
        for char_ord, old_value in reversed(self.catcode_old_values):
            state.tokenizer.set_catcode(char_ord, old_value)

        # Restore old register values
        for change in reversed(self.register_old_values):
            name, reg_id, value = change
            if value is None:
                state.registers.delete_register(name, reg_id)
            else:
                state.registers.set_register(name, reg_id, value)


class ExpanderState:
    """Manages the stack of StateLayer objects."""

    def __init__(self, tokenizer: Tokenizer):
        # Initialize with the base global state layer
        self._stack: List[StateLayer] = [StateLayer()]
        self.tokenizer = tokenizer
        self.pending_global = False

        self.registers = TexRegisters()
        # Add CounterManager instance
        self.counter_manager = CounterManager(self.registers)

        self.environment_registry: Dict[str, EnvironmentDefinition] = {}

        self._env_stack: List[str] = []

        self._catcode_text_mode_values: List[Tuple[int, Catcode]] = []

    @property
    def mode(self) -> ProcessingMode:
        return self.current.mode

    @mode.setter
    def mode(self, value: ProcessingMode):
        self.current.mode = value

    @property
    def is_math_mode(self) -> bool:
        return self.current.mode == ProcessingMode.MATH

    @is_math_mode.setter
    def is_math_mode(self, value: bool):
        self.set_mode(ProcessingMode.MATH if value else ProcessingMode.TEXT)

    def set_mode(self, mode: ProcessingMode):
        """Set the mode for the current scope."""
        is_same = mode == self.current.mode
        if not is_same:
            if mode == ProcessingMode.MATH:
                self._set_math_catcode_values()
            else:
                self._unset_math_catcode_values()
            self.current.mode = mode

    def _set_math_catcode_values(self):
        # Store original catcodes and set to ACTIVE
        for chars in ["_", "^", "&"]:
            char_ord = ord(chars)
            old_catcode = self.get_catcode(char_ord)
            # Only store and change if not already ACTIVE
            if old_catcode != Catcode.ACTIVE:
                self._catcode_text_mode_values.append((char_ord, old_catcode))
                self.tokenizer.set_catcode(char_ord, Catcode.ACTIVE)

    def _unset_math_catcode_values(self):
        for ord_char, old_catcode in self._catcode_text_mode_values:
            self.tokenizer.set_catcode(ord_char, old_catcode)
        self._catcode_text_mode_values.clear()  # Clear the list after restoring values

    # --- Stack Management ---
    def get_root(self) -> StateLayer:
        """Get the root state layer (the first layer in the stack)."""
        return self._stack[0]

    @property
    def current(self) -> StateLayer:
        """Get the currently active state layer (top of the stack)."""
        if not self._stack:
            raise RuntimeError("ExpanderState stack is empty!")
        return self._stack[-1]

    @property
    def current_env(self) -> Optional[str]:
        """Get the current environment stack."""
        return self._env_stack[-1] if self._env_stack else None

    def push_env_stack(self, env_name: str):
        """Pushes a new environment stack onto the stack, starting a new scope."""
        self._env_stack.append(env_name)

    def pop_env_stack(self):
        """Pops the current environment stack from the stack, ending the current scope."""
        if self._env_stack:
            self._env_stack.pop()

    def push_scope(self):
        """Pushes a new state layer onto the stack, starting a new scope."""
        # Create a new layer, inheriting from the current layer
        new_layer = StateLayer(parent=self.current)
        self._stack.append(new_layer)

    def pop_scope(self):
        """Pops the current state layer from the stack, ending the current scope."""
        if len(self._stack) <= 1:
            # Cannot pop the base global scope
            print("[WARNING]: Cannot pop the base ExpanderState scope!")
            return
        last_state = self._stack.pop()
        last_state.apply_old_values_to_state(self)

    # MACROS
    def get_macro(self, name: str) -> Optional[Macro]:
        return self.current.get_macro(name)

    def get_all_macros(self) -> Dict[str, Macro]:
        return self.current.macro_registry.get_all_macros()

    def set_macro(self, name: str, definition: Macro, is_global: bool = False):
        self.current.set_macro(name, definition, is_global or self.pending_global)
        self.pending_global = False

    # CATCODES
    def set_catcode(self, char_ord: int, catcode: Catcode):
        if not self.pending_global:
            self.current.store_catcode_old_value(char_ord, self.get_catcode(char_ord))
        self.tokenizer.set_catcode(char_ord, catcode)
        self.pending_global = False

    def get_catcode(self, char_ord: int) -> Catcode:
        return self.tokenizer.get_catcode(char_ord)

    # REGISTERS
    def get_register(
        self, reg_type: RegisterType, reg_id: Union[int, str], return_default=False
    ) -> Any:
        out = self.registers.get_register_value(reg_type, reg_id)
        if out is None and return_default:
            return RegisterType.get_default_value(reg_type)
        return out

    def set_register(
        self,
        register_type: RegisterType,
        reg_id: Union[int, str],
        value: Any,
        is_global: bool = False,
    ):
        is_global = self.pending_global or is_global
        if not is_global:
            self._store_register_old_value(register_type, reg_id)
        self.registers.set_register(register_type, reg_id, value)
        self.pending_global = False

    def increment_register(
        self, register_type: RegisterType, reg_id: Union[int, str], increment: Any
    ):
        # apparently all incr actions are global in latex, so no need to check global/old value
        self.registers.increment_register(register_type, reg_id, increment)

    def _store_register_old_value(
        self, register_type: RegisterType, reg_id: Union[int, str]
    ):
        cur_value = self.registers.get_register_value(
            register_type, reg_id
        )  # could be None
        # store changes (None means delete when undoing)
        self.current.register_old_values.append((register_type, reg_id, cur_value))

    # COUNTERS
    def has_counter(self, name: str) -> bool:
        return self.counter_manager.has_counter(name)

    def new_counter(self, name: str, parent: Optional[str] = None) -> None:
        """Create a new counter with optional parent relationship"""
        self.counter_manager.new_counter(name, parent)

    def step_counter(self, name: str) -> None:
        """Increment counter by 1 and reset all children"""
        self.counter_manager.step_counter(name)

    def set_counter(self, name: str, value: int) -> None:
        """Set counter value"""
        self.counter_manager.set_counter(name, value)

    def add_to_counter(self, name: str, increment: int) -> None:
        """Add to counter value"""
        self.counter_manager.add_to_counter(name, increment)

    def get_counter_value(self, name: str) -> Optional[int]:
        """Get current counter value"""
        return self.counter_manager.get_counter_value(name)

    def get_counter_as_format(
        self,
        name: str,
        style: Union[str, CounterFormat] = CounterFormat.ARABIC,
        hierarchy: bool = True,
    ) -> str:
        """Format counter value according to style"""
        return self.counter_manager.get_counter_as_format(name, style, hierarchy)

    def counter_within(self, name: str, parent: Optional[str] = None) -> None:
        """Set the counter to be within the parent counter"""
        self.counter_manager.counter_within(name, parent)

    # NEW: ENVIRONMENT DEFINITION MANAGEMENT
    def get_environment_definition(self, name: str) -> Optional[EnvironmentDefinition]:
        """Get a global environment definition."""
        return self.environment_registry.get(name)

    def set_environment_definition(self, name: str, definition: EnvironmentDefinition):
        """Set a global environment definition (as newenvironment is global)."""
        # No 'is_global' parameter here, as it's inherently global for environment definitions
        self.environment_registry[name] = definition
