from logging import Logger
import logging
from typing import Dict, List, Set, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from latex2json.registers.types import RegisterType, CounterFormat
from latex2json.registers.registers import TexRegisters
from latex2json.registers.utils import int_to_roman, int_to_alpha


@dataclass
class CounterInfo:
    """Information about a LaTeX counter"""

    name: str
    parent: Optional[str] = None
    children: List[str] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []


class CounterManager:
    """Manages LaTeX counters with parent-child relationships"""

    def __init__(self, tex_registers: TexRegisters, logger: Optional[Logger] = None):
        self.registers = tex_registers
        self.counters: Dict[str, CounterInfo] = {}
        self.logger = logger or logging.getLogger(__name__)
        self._counter_prefix = "c@"

        # Initialize built-in counters with relationships
        self._init_builtin_counters()

    def _init_builtin_counters(self):
        """Initialize common LaTeX counters"""
        # Independent counters
        self.new_counter("page")
        self.new_counter("equation")
        self.new_counter("footnote")
        self.new_counter("figure")
        self.new_counter("table")

        # Sectioning hierarchy
        self.new_counter("part")
        self.new_counter("chapter", parent="part")
        self.new_counter("section", parent="chapter")
        self.new_counter("subsection", parent="section")
        self.new_counter("subsubsection", parent="subsection")
        self.new_counter("paragraph", parent="subsubsection")
        self.new_counter("subparagraph", parent="paragraph")

        # Enumerate counters (nested lists)
        self.new_counter("enumi")
        self.new_counter("enumii", parent="enumi")
        self.new_counter("enumiii", parent="enumii")
        self.new_counter("enumiv", parent="enumiii")

    def _get_internal_name(self, counter_name: str) -> str:
        """Convert a user-facing counter name to internal register name"""
        return f"{self._counter_prefix}{counter_name}"

    def new_counter(self, name: str, parent: Optional[str] = None) -> None:
        """Create a new counter with optional parent relationship"""
        if name in self.counters:
            self.logger.warning(f"Counter '{name}' already exists")
            return
            # raise ValueError(f"Counter '{name}' already exists")

        # Validate parent exists
        if parent and parent not in self.counters:
            self.logger.warning(f"Parent counter '{parent}' does not exist")
            return
            # raise ValueError(f"Parent counter '{parent}' does not exist")

        # Create counter info
        counter_info = CounterInfo(name=name, parent=parent)
        self.counters[name] = counter_info

        # Add to parent's children list
        if parent:
            self.counters[parent].children.append(name)

        # Initialize the actual register storage
        self.registers.set_register(
            RegisterType.COUNT, self._get_internal_name(name), 0
        )

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
        counter_info = self.counters[parent_name]

        for child_name in counter_info.children:
            # Reset the child counter
            self.set_counter(child_name, 0)

            # Recursively reset grandchildren
            self._reset_children(child_name)

    def get_counter_value(self, name: str) -> Optional[int]:
        """Get current counter value"""
        if name not in self.counters:
            return None

        value = self.registers.get_register_value(
            RegisterType.COUNT, self._get_internal_name(name)
        )
        return value if value is not None else 0

    def get_counter_hierarchy(self, name: str) -> List[str]:
        """Get the full hierarchy path for a counter (parent -> child)"""
        if name not in self.counters:
            return []

        hierarchy = []
        current = name

        # Build hierarchy from bottom up
        while current:
            hierarchy.insert(0, current)
            current = self.counters[current].parent

        return hierarchy

    def get_all_children(self, name: str) -> Set[str]:
        """Get all descendants of a counter (children, grandchildren, etc.)"""
        if name not in self.counters:
            return set()

        descendants = set()

        def collect_descendants(parent: str):
            for child in self.counters[parent].children:
                descendants.add(child)
                collect_descendants(child)

        collect_descendants(name)
        return descendants

    def format_counter(
        self, name: str, style: Union[str, CounterFormat] = CounterFormat.ARABIC
    ) -> str:
        """Format counter value according to style"""
        value = self.get_counter_value(name)
        format_type = CounterFormat.from_str(style)

        match format_type:
            case CounterFormat.ARABIC:
                return str(value)
            case CounterFormat.ROMAN:
                return int_to_roman(value, lowercase=True)
            case CounterFormat.ROMAN_UPPER:
                return int_to_roman(value, lowercase=False)
            case CounterFormat.ALPHA:
                return int_to_alpha(value, lowercase=True)
            case CounterFormat.ALPHA_UPPER:
                return int_to_alpha(value, lowercase=False)

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
                print_counter(child, indent + 1)

        for root in sorted(roots):
            print_counter(root)

        return "\n".join(lines)


# Demo of the hierarchy in action
if __name__ == "__main__":
    pass

    register = TexRegisters()
    counter_manager = CounterManager(register)
    print(counter_manager.debug_hierarchy())
    # system = LaTeXCounterSystem()

    # # Simulate some LaTeX operations
    # print("=== Initial State ===")
    # print(system.counters.debug_hierarchy())

    # print("\n=== After \\stepcounter{chapter} ===")
    # system.counters.step_counter("chapter")
    # print(system.counters.debug_hierarchy())

    # print("\n=== After \\stepcounter{section} twice ===")
    # system.counters.step_counter("section")
    # system.counters.step_counter("section")
    # print(system.counters.debug_hierarchy())

    # print("\n=== After \\stepcounter{subsection} ===")
    # system.counters.step_counter("subsection")
    # print(system.counters.debug_hierarchy())

    # print("\n=== After \\stepcounter{section} (resets subsection) ===")
    # system.counters.step_counter("section")
    # print(system.counters.debug_hierarchy())
