from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from latex2json.latex_maps.fonts import FontAttributes, FontStyle, FontStyleType


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
        self.font: FontAttributes = parent.font.copy() if parent else FontAttributes()
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
        # parent_font = self.parent.font if self.parent else DEFAULT_FONT

        # Check each font attribute against parent (or default if no parent)
        if font.series.value != DEFAULT_FONT.series.value:
            styles.append(font.series.value)
        if font.shape.value != DEFAULT_FONT.shape.value:
            styles.append(font.shape.value)
        if font.size.value != DEFAULT_FONT.size.value:
            styles.append(font.size.value)
        if font.family.value != DEFAULT_FONT.family.value:
            styles.append(font.family.value)
        if font.color != DEFAULT_FONT.color:
            styles.append(f"color={font.color}")

        return styles

    def __repr__(self) -> str:
        parent_name = self.parent.__class__.__name__ if self.parent else "None"
        return (
            f"ParserStateLayer(font={self.font.series.value}, "
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

    @property
    def current(self) -> ParserStateLayer:
        """Get the currently active parser state layer (top of the stack)."""
        if not self._stack:
            raise RuntimeError("ParserState stack is empty!")
        return self._stack[-1]

    # --- Scope Management ---
    def push_scope(self):
        """
        Pushes a new parser state layer onto the stack, creating a new scope.
        Optionally sets the current AST node for this new scope.
        """
        new_layer = ParserStateLayer(parent=self.current)
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

    # --- Methods to Modify State (Delegated to current layer) ---
    def set_font_series(self, series: FontStyle):
        self.current.font.series = series

    def set_font_shape(self, shape: FontStyle):
        self.current.font.shape = shape

    def set_font_size(self, size: FontStyle):
        self.current.font.size = size

    def set_font_family(self, family: FontStyle):
        self.current.font.family = family

    def set_font_color(self, color_hex: str):
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

    def set_font(self, style: FontStyle):
        """Set font attribute based on FontStyle, toggling back to default if same style is set"""
        if style.type == FontStyleType.SERIES:
            if self.current.font.series.value == style.value:
                self.set_font_series(DEFAULT_FONT.series)
            else:
                self.set_font_series(style)
        elif style.type == FontStyleType.SHAPE:
            if self.current.font.shape.value == style.value:
                self.set_font_shape(DEFAULT_FONT.shape)
            else:
                self.set_font_shape(style)
        elif style.type == FontStyleType.SIZE:
            if self.current.font.size.value == style.value:
                self.set_font_size(DEFAULT_FONT.size)
            else:
                self.set_font_size(style)
        elif style.type == FontStyleType.FAMILY:
            if self.current.font.family.value == style.value:
                self.set_font_family(DEFAULT_FONT.family)
            else:
                self.set_font_family(style)
