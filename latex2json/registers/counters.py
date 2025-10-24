from logging import Logger
import logging
from typing import Dict, List, Set, Optional, Any, Union
from dataclasses import dataclass
from latex2json.registers.types import RegisterType, CounterFormat
from latex2json.registers.registers import TexRegisters


@dataclass
class CounterInfo:
    """Information about a LaTeX counter implemented as a tree node"""

    name: str
    _parent: Optional["CounterInfo"] = None
    _children: List["CounterInfo"] = None
    style: CounterFormat = CounterFormat.ARABIC
    skip_parent_zeros: bool = True

    def __post_init__(self):
        if self._children is None:
            self._children = []

    @property
    def parent(self) -> Optional["CounterInfo"]:
        return self._parent

    @parent.setter
    def parent(self, new_parent: Optional["CounterInfo"]) -> None:
        # Remove from old parent's children
        if self._parent is not None:
            self._parent._children.remove(self)

        # Set new parent
        self._parent = new_parent

        # Add to new parent's children
        if new_parent is not None:
            new_parent._children.append(self)

    @property
    def children(self) -> List["CounterInfo"]:
        return self._children.copy()  # Return copy to prevent direct modification

    def add_child(self, child: "CounterInfo") -> None:
        """Add a child node, handling parent relationship"""
        if child not in self._children:
            child.parent = self  # This will handle both sides of the relationship

    def remove_child(self, child: "CounterInfo") -> None:
        """Remove a child node, handling parent relationship"""
        if child in self._children:
            child.parent = None  # This will handle both sides of the relationship

    def get_styled_value(self, value: int) -> str:
        format_type = CounterFormat.from_str(self.style)
        return format_type.format_value(value)


class CounterManager:
    """Manages LaTeX counters with parent-child relationships"""

    def __init__(self, tex_registers: TexRegisters, logger: Optional[Logger] = None):
        self.registers = tex_registers
        self.counters: Dict[str, CounterInfo] = {}
        self.logger = logger or logging.getLogger(__name__)
        self._counter_prefix = "c@"

        # Initialize built-in counters with relationships
        self._init_builtin_counters()

    def _init_section_counters(self):
        self.new_counter("part", style=CounterFormat.ROMAN_UPPER, check_exists=False)

        # Sectioning hierarchy
        SECTIONS = [
            "chapter",
            "section",
            "subsection",
            "subsubsection",
            "paragraph",
            "subparagraph",
        ]

        for i, section in enumerate(SECTIONS):
            if i > 0:
                self.new_counter(section, parent=SECTIONS[i - 1], check_exists=False)
            else:
                self.new_counter(section, check_exists=False)

    def _init_builtin_counters(self):
        """Initialize common LaTeX counters"""
        self._init_section_counters()

        # Independent counters
        self.new_counter("page")
        self.new_counter("equation")
        # subequation counter does not necessarily exist in latex, but we do this for subequations
        self.new_counter("subequation", parent="equation", style=CounterFormat.ALPHA)
        self.new_counter("footnote")
        self.new_counter("figure")
        self.new_counter("subfigure", parent="figure", style=CounterFormat.ALPHA)
        self.new_counter("table")
        self.new_counter("subtable", parent="table", style=CounterFormat.ALPHA)
        self.new_counter("algorithm")

        # enum
        self.new_counter("enumi")  # enumerate level 1
        self.new_counter("enumii")  # enumerate level 2
        self.new_counter("enumiii")  # enumerate level 3
        self.new_counter("enumiv")  # enumerate level 4

        # other
        self.new_counter("@topnum")
        self.new_counter("@mpfn")

    def reset_section_counters(self):
        self._init_section_counters()

    def get_counters(self, internal_name=True):
        out = []
        for counter in self.counters.keys():
            if internal_name:
                out.append(self._get_internal_name(counter))
            else:
                out.append(counter)
        return out

    def _get_internal_name(self, counter_name: str) -> str:
        """Convert a user-facing counter name to internal register name"""
        if counter_name.startswith(self._counter_prefix) or counter_name.startswith(
            "@"
        ):
            return counter_name
        return f"{self._counter_prefix}{counter_name}"

    def _get_base_name(self, counter_name: str) -> str:
        """Get the base name of a counter (without the prefix)"""
        if counter_name.startswith(self._counter_prefix):
            return counter_name[len(self._counter_prefix) :]
        return counter_name

    def has_counter(self, name: str) -> bool:
        return name in self.counters

    def new_counter(
        self,
        name: str,
        parent: Optional[str] = None,
        style: CounterFormat = CounterFormat.ARABIC,
        check_exists: bool = True,
    ) -> CounterInfo:
        """Create a new counter with optional parent relationship"""
        if check_exists and name in self.counters:
            return self.counters[name]

        # Create counter info
        counter_info = CounterInfo(name=name, style=style)
        self.counters[name] = counter_info

        # Set up parent relationship if specified
        if parent:
            if parent not in self.counters:
                self.logger.warning(f"Parent counter '{parent}' does not exist")
                return counter_info
            self.counters[parent].add_child(counter_info)

        # Initialize the actual register storage
        self.registers.set_register(
            RegisterType.COUNT, self._get_internal_name(name), 0
        )

        return counter_info

    def set_counter(self, name: str, value: int) -> None:
        """Set counter value"""
        # if name not in self.counters:
        #     raise ValueError(f"Counter '{name}' does not exist")

        self.registers.set_register(
            RegisterType.COUNT, self._get_internal_name(name), value
        )

    def add_to_counter(self, name: str, increment: int) -> None:
        """Add to counter value"""
        # if name not in self.counters:
        #     raise ValueError(f"Counter '{name}' does not exist")

        self.registers.increment_register(
            RegisterType.COUNT, self._get_internal_name(name), increment
        )

    def step_counter(self, name: str) -> None:
        """Increment counter by 1 and reset all children"""
        # if name not in self.counters:
        #     raise ValueError(f"Counter '{name}' does not exist")

        # Increment this counter
        self.add_to_counter(name, 1)

        # Reset all child counters recursively
        self._reset_children(name)

    def _reset_children(self, parent_name: str) -> None:
        """Recursively reset all child counters to 0"""
        counter_info = self.counters.get(parent_name)
        if not counter_info:
            return

        for child in counter_info.children:
            # Reset the child counter
            self.set_counter(child.name, 0)

            # Recursively reset grandchildren
            self._reset_children(child.name)

    def get_counter_value(self, name: str) -> Optional[int]:
        """Get current counter value"""
        if name not in self.counters:
            return None

        value = self.registers.get_register_value(
            RegisterType.COUNT, self._get_internal_name(name)
        )
        return value

    def get_counter_formatted_value(self, name: str) -> Optional[str]:
        value = self.get_counter_value(name)
        if value is None:
            return None
        return self.counters[name].get_styled_value(value)

    def get_counter_hierarchy(self, name: str) -> List[str]:
        """Get the full hierarchy path for a counter (parent -> child)"""
        if name not in self.counters:
            return []

        hierarchy = []
        current = self.counters[name]

        # Build hierarchy from bottom up
        while current:
            hierarchy.insert(0, current.name)
            current = current.parent

        return hierarchy

    def get_all_children(self, name: str) -> Set[str]:
        """Get all descendants of a counter (children, grandchildren, etc.)"""
        if name not in self.counters:
            return set()

        descendants = set()
        counter = self.counters[name]

        def collect_descendants(node: CounterInfo):
            for child in node.children:
                descendants.add(child.name)
                collect_descendants(child)

        collect_descendants(counter)
        return descendants

    def get_counter_info(self, name: str) -> Optional[CounterInfo]:
        if name not in self.counters:
            return None
        return self.counters[name]

    def get_counter_display(
        self,
        name: str,
        hierarchy: bool = True,
    ) -> str:
        """Format counter value according to each counter's style

        Args:
            name: Counter name to format
            hierarchy: If True, include parent counter values (e.g. 2.1.3)
        """
        if not name in self.counters:
            return ""

        counter_info = self.counters[name]
        has_parent = counter_info.parent is not None
        if hierarchy and has_parent:
            # Get full hierarchy path from root to this counter
            hierarchy_path = self.get_counter_hierarchy(name)
            hierarchy_values: List[str] = []

            # Format each counter value in the hierarchy using its own style
            for counter_str in hierarchy_path:
                if counter_str == "part":
                    continue
                value = self.get_counter_value(counter_str)
                if value is not None:
                    if (
                        counter_str != name
                        and value == 0
                        and len(hierarchy_values) == 0
                    ):
                        # skip 0 values if no existing values yet
                        continue
                    hierarchy_values.append(
                        self.get_counter_formatted_value(counter_str)
                    )

            out_str = ".".join(hierarchy_values)
            if not counter_info.skip_parent_zeros and len(hierarchy_values) < 2:
                out_str = "0." + out_str
            return out_str

        # Single counter formatting
        value = self.get_counter_formatted_value(name)
        return value or ""

    def debug_hierarchy(self) -> str:
        """Generate a debug representation of the counter hierarchy"""
        lines = []

        # Find root counters (those without parents)
        roots = [name for name, info in self.counters.items() if info.parent is None]

        def print_counter(name: str, indent: int = 0) -> None:
            value = self.get_counter_value(name)
            prefix = "  " * indent
            lines.append(f"{prefix}{name}: {value}")

            # Print children
            for child in self.counters[name].children:
                print_counter(child.name, indent + 1)

        for root in sorted(roots):
            print_counter(root)

        return "\n".join(lines)

    def counter_within(self, counter: str, parent: Optional[str] = None) -> None:
        r"""Make counter subordinate to parent or remove parent relationship (like \counterwithin, \numberwithin and \counterwithout)

        Args:
            counter: The counter to modify
            parent: The new parent counter, or None to remove from current parent
        """
        if counter not in self.counters:
            self.logger.warning(f"Counter '{counter}' does not exist")
            return

        if parent is not None and parent not in self.counters:
            self.logger.warning(f"Parent counter '{parent}' does not exist")
            return

        counter_info = self.counters[counter]
        parent_node = self.counters[parent] if parent is not None else None

        # The parent setter will handle all the relationship updates
        counter_info.parent = parent_node
        counter_info.skip_parent_zeros = False


# Demo of the hierarchy in action
if __name__ == "__main__":

    register = TexRegisters()
    counter_manager = CounterManager(register)
    print(counter_manager.debug_hierarchy())
