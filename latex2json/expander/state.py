import enum
from logging import Logger
import logging
from typing import List, Optional, Dict, Any, Tuple, Union

from latex2json.expander.macro_registry import Macro, MacroRegistry
from latex2json.latex_maps.environments import EnvironmentDefinition
from latex2json.registers import RegisterType, TexRegisters
from latex2json.registers.types import CounterFormat
from latex2json.tokens.catcodes import Catcode, MATHMODE_CATCODES
from latex2json.tokens.tokenizer import Tokenizer
from latex2json.registers.counters import CounterInfo, CounterManager
from latex2json.tokens.types import Token


class ProcessingMode(enum.Enum):
    TEXT = 1
    MATH_INLINE = 3  # Simulate Catcode.Mathshift=3 / TokenType.MATH_SHIFT_INLINE
    MATH_DISPLAY = 4  # Simulate TokenType.MATH_SHIFT_DISPLAY
    # ... other modes


class StateLayer:
    """Represents the state for a single scope layer."""

    def __init__(self, parent: Optional["StateLayer"] = None):
        self._parent = parent

        # --- State that might not be strictly layered but is part of the scope ---
        # Mode: Often copied, but changes are local
        # self.mode: ProcessingMode = parent.mode if parent else ProcessingMode.TEXT

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

    def get_macro(self, name: str, is_active_char=False) -> Optional[Macro]:
        return self.macro_registry.get(name, is_active_char=is_active_char)

    def set_macro(
        self,
        name: str,
        definition: Macro,
        is_global: bool = False,
        is_active_char=False,
    ):
        self.macro_registry.set(
            name, definition, is_global, is_active_char=is_active_char
        )

    def delete_macro(self, name: str, is_global: bool = True, is_active_char=False):
        self.macro_registry.delete(name, is_global, is_active_char=is_active_char)

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

    def __init__(self, tokenizer: Tokenizer, logger: Optional[Logger] = None):
        # Initialize with the base global state layer
        self._stack: List[StateLayer] = [StateLayer()]
        self.logger = logger or logging.getLogger(__name__)
        self.tokenizer = tokenizer

        # registers and counters
        self.registers = TexRegisters()
        self.counter_manager = CounterManager(self.registers)

        # registries
        self.environment_registry: Dict[str, EnvironmentDefinition] = {}
        self.font_registry: Dict[str, List[Token]] = {}
        self.color_registry: Dict[str, str] = {}  # e.g. "red" -> "rgb(1,0,0)"

        # storage
        self._catcode_text_mode_values: List[Tuple[int, Catcode]] = []

        # mode
        self._mode_stack: List[ProcessingMode] = [ProcessingMode.TEXT]

        # variable states
        self.pending_global = False
        # self.is_verbatim_mode = False

        # collect frontmatter tokens and only emit on \maketitle
        self.frontmatter: Dict[str, List[Token]] = {
            "title": [],
            "author": [],
            "date": [],
            "thanks": [],
        }

        self.protected_frontmatter_commands: set[str] = {
            "\\@" + key for key in self.frontmatter.keys()
        }

        # appendix
        self.in_appendix = False

        # package/class
        self.in_package_or_class = False

        # in subequations
        self.in_subequations = False

    @property
    def mode(self) -> ProcessingMode:
        return self._mode_stack[-1]

    @property
    def is_math_mode(self) -> bool:
        return self.check_is_math_mode(self.mode)

    @staticmethod
    def check_is_math_mode(mode: ProcessingMode) -> bool:
        return mode in [ProcessingMode.MATH_INLINE, ProcessingMode.MATH_DISPLAY]

    # appendix
    def set_is_appendix(self, is_appendix: bool):
        if is_appendix == self.in_appendix:
            return
        self.in_appendix = is_appendix

        # reset all section counters
        self.counter_manager.reset_section_counters()

        TOP_SECTION = "section"
        counter = self.counter_manager.counters.get(TOP_SECTION)
        if counter:
            if is_appendix:
                counter.style = CounterFormat.ALPHA_UPPER
            else:
                counter.style = CounterFormat.ARABIC

    def set_in_subequations(self, in_subequations: bool):
        if in_subequations == self.in_subequations:
            return
        self.in_subequations = in_subequations
        if in_subequations:
            # incr equation counter
            self.counter_manager.step_counter("equation")

    def push_mode(self, mode: ProcessingMode):
        """Push a new mode onto the stack."""
        self._mode_stack.append(mode)
        self._set_mode_values()

    def pop_mode(self):
        """Pop the current mode and restore the previous one."""
        if len(self._mode_stack) <= 1:
            return
            # raise RuntimeError("Cannot pop the base mode")
        self._mode_stack.pop()
        self._set_mode_values()

    def toggle_mode(self, mode: ProcessingMode):
        if self.mode == mode:
            self.pop_mode()
        else:
            self.push_mode(mode)

    def _set_mode_values(self):
        if self.is_math_mode:
            self._set_math_catcode_values()
        else:
            self._unset_math_catcode_values()

    def _set_math_catcode_values(self):
        # Store original catcodes, then set
        for char_ord, catcode in MATHMODE_CATCODES.items():
            old_catcode = self.get_catcode(char_ord)
            if old_catcode != catcode:
                self._catcode_text_mode_values.append((char_ord, old_catcode))
                self.tokenizer.set_catcode(char_ord, catcode)

    def _unset_math_catcode_values(self):
        for char_ord, old_catcode in self._catcode_text_mode_values:
            self.tokenizer.set_catcode(char_ord, old_catcode)
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

    def push_scope(self):
        """Pushes a new state layer onto the stack, starting a new scope."""
        # Create a new layer, inheriting from the current layer
        new_layer = StateLayer(parent=self.current)
        self._stack.append(new_layer)

    def pop_scope(self):
        """Pops the current state layer from the stack, ending the current scope."""
        if len(self._stack) <= 1:
            # Cannot pop the base global scope
            self.logger.info("Cannot pop the base ExpanderState scope!")
            return
        last_state = self._stack.pop()
        last_state.apply_old_values_to_state(self)

    # MACROS
    def get_macro(self, name: str, is_active_char=False) -> Optional[Macro]:
        return self.current.get_macro(name, is_active_char=is_active_char)

    def get_all_macros(self) -> Dict[str, Macro]:
        return self.current.macro_registry.get_all_macros()

    def set_macro(
        self,
        name: str,
        macro: Macro,
        is_global: bool = False,
        is_active_char=False,
    ):
        self.current.set_macro(
            name,
            macro,
            is_global or self.pending_global,
            is_active_char=is_active_char,
        )
        self.pending_global = False

    def delete_macro(self, name: str, is_global: bool = True, is_active_char=False):
        self.current.delete_macro(
            name, is_global=is_global, is_active_char=is_active_char
        )

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

    def create_register(
        self,
        register_type: RegisterType,
        reg_id: Union[int, str],
        default_value: Optional[Any] = None,
    ):
        self.registers.create_register(register_type, reg_id, default_value)

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

    def step_counter(self, name: str, strict=False) -> None:
        """Increment counter by 1 and reset all children"""
        if not strict:
            if name == "equation" and self.in_subequations:
                name = "subequation"
        self.counter_manager.step_counter(name)

    def get_counter_display(self, name: str, strict=False, hierarchy=True) -> str:
        if not strict:
            if name == "equation" and self.in_subequations:
                name = "subequation"
        return self.counter_manager.get_counter_display(name, hierarchy=hierarchy)

    def get_counter_info(self, name: str) -> Optional[CounterInfo]:
        return self.counter_manager.get_counter_info(name)

    def set_counter(self, name: str, value: int) -> None:
        """Set counter value"""
        self.counter_manager.set_counter(name, value)

    def add_to_counter(self, name: str, increment: int) -> None:
        """Add to counter value"""
        self.counter_manager.add_to_counter(name, increment)

    def get_counter_value(self, name: str) -> Optional[int]:
        """Get current counter value"""
        return self.counter_manager.get_counter_value(name)

    def get_counters(self, with_prefix=True):
        return self.counter_manager.get_counters(with_prefix)

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
