import enum
import dataclasses
from typing import List, Optional, Dict, Any, Tuple, Callable, Union

from latex2json.expander.macro_registry import Macro, MacroRegistry
from latex2json.tokens import Catcode, get_default_catcodes
from latex2json.tokens.tokenizer import Tokenizer

# --- Assume Placeholder Definitions from MacroRegistry code are available ---
# Token, TokenType, Catcode, ASTNode, CommandNode, TextNode, BraceNode, EnvironmentNode
# MacroRegistry, CommandDefinition, PrimitiveDefinition, MacroDefinition

# --- Placeholder State Components ---


class ProcessingMode(enum.Enum):
    TEXT = 1
    MATH = 2
    # ... other modes


@dataclasses.dataclass
class ConditionalState:
    # Tracks the state of \if...\fi conditionals (e.g., stack of boolean states)
    # This is a simplified placeholder. Real conditional state is complex.
    is_true: bool = True  # Are we currently in a 'true' branch?
    # Add stack for nested conditionals, tracking if we are skipping content etc.

    def copy(self) -> "ConditionalState":
        # Return a copy for new state layers
        return ConditionalState(is_true=self.is_true)  # Simplified copy


# --- StateLayer Class ---


class StateLayer:
    """Represents the state for a single scope layer."""

    def __init__(self, parent: Optional["StateLayer"] = None):
        self._parent = parent

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

        # Local Register Assignments: Track assignments made in this scope
        # This is a simplified model. TeX's register assignment is complex (\global).
        # A real implementation might have a global register bank, and StateLayer
        # just tracks assignments that are local to this scope.
        self.local_register_assignments: Dict[str, Any] = {}  # e.g., {"count0": 10}

        # --- State that might not be strictly layered but is part of the scope ---
        # Mode: Often copied, but changes are local
        self.mode: ProcessingMode = parent.mode if parent else ProcessingMode.TEXT

        # Conditional State: Often needs its own stack or complex logic within the layer
        # Changes to conditional state are local to the group they occur in.
        self.conditional_state: ConditionalState = (
            parent.conditional_state.copy() if parent else ConditionalState()
        )

        # # Parameter Values: Copied, local changes don't affect parent
        # self.parameter_values: Dict[str, Any] = (
        #     parent.parameter_values.copy()
        #     if parent
        #     else self._initialize_default_parameters()
        # )

        # # Font Information: Copied, local changes don't affect parent
        # self.font_information: Any = (
        #     parent.font_information if parent else self._initialize_default_font()
        # )

        # # Language Settings: Copied, local changes don't affect parent
        # self.language_settings: Any = (
        #     parent.language_settings if parent else self._initialize_default_language()
        # )

    def get_catcode(self, char_ord: int) -> Catcode:
        """Get the catcode for a character from this layer's table."""
        return self.catcode_table.get(
            char_ord, Catcode.OTHER
        )  # Default to OTHER if not found

    def set_catcode(self, char_ord: int, catcode: Catcode):
        """Set the catcode for a character in this layer's table."""
        self.catcode_table[char_ord] = catcode

    # def _initialize_default_parameters(self) -> Dict[str, Any]:
    #     # Initialize with default TeX parameter values
    #     return {
    #         "parindent": 15.0,  # Example dimension value
    #         "baselineskip": 12.0,  # Example dimension value
    #         # ... other parameters
    #     }

    # def _initialize_default_font(self) -> Any:
    #     # Placeholder for default font information
    #     return "default_font"

    # def _initialize_default_language(self) -> Any:
    #     # Placeholder for default language settings
    #     return "english"

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
        self._stack.pop()
        self.tokenizer.set_catcode_table(self.current.catcode_table)

    # --- Convenience methods to access state from the current layer ---

    @property
    def registry(self) -> MacroRegistry:
        """Get the macro registry for the current scope."""
        return self.current.macro_registry

    def set_macro(self, name: str, definition: Macro, is_global: bool = False):
        """Set a macro in the current scope."""
        self.registry.set(name, definition, is_global)

    def get_macro(self, name: str) -> Optional[Macro]:
        """Get a macro from the current scope."""
        return self.registry.get(name)

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

    # Add convenience properties/methods for other current state (mode, conditionals, etc.)
    @property
    def mode(self) -> ProcessingMode:
        return self.current.mode

    @property
    def conditional_state(self) -> ConditionalState:
        return self.current.conditional_state

    # Add methods to get/set register values, parameter values, etc.,
    # which would interact with the current layer's state and potentially global state.
    # Example: get_register(name), set_register(name, value, is_global)
    # Example: get_parameter(name), set_parameter(name, value, is_global)
