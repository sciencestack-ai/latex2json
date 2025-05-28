from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field


# --- Define some basic attribute types (you'll expand these) ---
# Assuming these are enums or simple strings for now
class FontSeries:
    NORMAL = "normal"
    BOLD = "bold"


class FontShape:
    UPRIGHT = "upright"
    ITALIC = "italic"


class FontSize:
    NORMAL = "normal"
    LARGE = "large"
    # ... etc.


class FontFamily:
    ROMAN = "roman"
    SANS = "sans"
    TYPEWRITER = "typewriter"


@dataclass
class FontAttributes:
    """Represents the current font settings."""

    series: FontSeries = FontSeries.NORMAL
    shape: FontShape = FontShape.UPRIGHT
    size: FontSize = FontSize.NORMAL
    family: FontFamily = FontFamily.ROMAN
    color: Optional[str] = None  # e.g., "#000000" for black


@dataclass
class ListAttributes:
    """Represents settings for the current list environment."""

    level: int = 0  # Current nesting level of lists (0 for no list)
    item_label_style: str = "bullet"  # e.g., "bullet", "arabic", "alph"
    item_counter_value: int = 0  # The counter for the current list item


DEFAULT_FONT = FontAttributes()


# --- ParserStateLayer Class ---
class ParserStateLayer:
    """
    Represents a single layer of parser state, typically pushed/popped
    for TeX groups ({...}) or environments.
    """

    def __init__(self, parent: Optional["ParserStateLayer"] = None):
        self.parent = parent

        # --- Formatting Attributes (Inherited/Overridden) ---
        self.font: FontAttributes = parent.font if parent else FontAttributes()
        # You might have other formatting attributes like line spacing, indentation, etc.

        # --- List Attributes (Inherited/Overates) ---
        self.list_attributes: ListAttributes = (
            parent.list_attributes if parent else ListAttributes()
        )

        # --- Current AST Node Context ---
        # This points to the AST node that current content should be added to.
        # It's not inherited, but set by the parser when it creates a new structural node.
        self.current_ast_node: Optional[Any] = (
            None  # Type will be your AST node classes
        )

    def get_styles_as_string(self) -> List[str]:
        """
        Returns unique styles as a list of strings.
        """
        styles = []
        font = self.font

        # Get parent font attributes or default if no parent
        parent_font = self.parent.font if self.parent else DEFAULT_FONT

        # Check each font attribute against parent (or default if no parent)
        if font.series != parent_font.series:
            styles.append(font.series)

        if font.shape != parent_font.shape:
            styles.append(font.shape)

        if font.size != parent_font.size:
            styles.append(font.size)

        if font.family != parent_font.family:
            styles.append(font.family)

        if font.color != parent_font.color:
            styles.append(f"color={font.color}")

        return styles

    def __repr__(self) -> str:
        parent_name = self.parent.__class__.__name__ if self.parent else "None"
        return (
            f"ParserStateLayer(font={self.font.series}, "
            f"list_level={self.list_attributes.level}, "
            f"parent={parent_name})"
        )


class ParserState:
    """
    Manages the overall state for the Parser, including scoped attributes
    and global document-level data.
    """

    def __init__(self):
        # Stack of parser state layers for scoping
        self._stack: List[ParserStateLayer] = [
            ParserStateLayer()
        ]  # Start with a base layer

        # # Global registry for labels (accessible from anywhere in the document)
        # self.labels: Dict[str, LabelInfo] = {}

        # You might add other global registries here, e.g., for bibliography entries

    @property
    def current(self) -> ParserStateLayer:
        """Get the currently active parser state layer (top of the stack)."""
        if not self._stack:
            raise RuntimeError("ParserState stack is empty!")
        return self._stack[-1]

    # --- Scope Management ---
    def push_scope(self, new_node_context: Optional[Any] = None):
        """
        Pushes a new parser state layer onto the stack, creating a new scope.
        Optionally sets the current AST node for this new scope.
        """
        new_layer = ParserStateLayer(parent=self.current)
        if new_node_context:
            new_layer.current_ast_node = new_node_context
        self._stack.append(new_layer)

    def pop_scope(self):
        """Pops the current parser state layer from the stack, ending the current scope."""
        if len(self._stack) <= 1:
            print("[WARNING]: Cannot pop the base ParserState scope!")
            return
        self._stack.pop()

    # --- Accessors for Current Scope Attributes ---
    @property
    def font_attributes(self) -> FontAttributes:
        return self.current.font

    @property
    def list_attributes(self) -> ListAttributes:
        return self.current.list_attributes

    @property
    def current_ast_node(self) -> Optional[Any]:
        """The AST node that current content should be added to."""
        return self.current.current_ast_node

    def set_current_ast_node(self, node: Any):
        """Sets the current AST node for the active scope."""
        self.current.current_ast_node = node

    # --- Methods to Modify State (Delegated to current layer) ---
    def set_font_series(self, series: FontSeries):
        self.current.font.series = series

    def set_font_shape(self, shape: FontShape):
        self.current.font.shape = shape

    def set_font_size(self, size: FontSize):
        self.current.font.size = size

    def set_font_family(self, family: FontFamily):
        self.current.font.family = family

    def set_color(self, color_hex: str):
        self.current.font.color = color_hex

    def get_styles_as_string(self) -> List[str]:
        return self.current.get_styles_as_string()

    def set_list_level(self, level: int):
        self.current.list_attributes.level = level

    def set_item_label_style(self, style: str):
        self.current.list_attributes.item_label_style = style

    def set_item_counter_value(self, value: int):
        self.current.list_attributes.item_counter_value = value

    def __repr__(self) -> str:
        return f"ParserState(stack_depth={len(self._stack)})"
