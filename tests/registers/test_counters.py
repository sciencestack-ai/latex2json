import pytest

from latex2json.registers import CounterManager, TexRegisters
from latex2json.registers.types import CounterFormat


def test_counter_manager_basics():
    registers = TexRegisters()
    manager = CounterManager(registers)

    # Test counter creation and values
    manager.new_counter("mycounter")
    assert manager.get_counter_value("mycounter") == 0

    manager.set_counter("mycounter", 42)
    assert manager.get_counter_value("mycounter") == 42

    # Test parent-child relationship
    manager.new_counter("child", parent="mycounter")
    manager.set_counter("child", 5)
    assert manager.get_counter_value("child") == 5

    # Test stepping counter (should reset children)
    manager.step_counter("mycounter")
    assert manager.get_counter_value("mycounter") == 43
    assert manager.get_counter_value("child") == 0

    manager.add_to_counter("mycounter", -3)
    assert manager.get_counter_value("mycounter") == 40


def test_counter_hierarchy():
    registers = TexRegisters()
    manager = CounterManager(registers)

    # Test built-in counter relationships
    hierarchy = manager.get_counter_hierarchy("subsection")
    assert hierarchy == ["part", "chapter", "section", "subsection"]

    # Test getting all children
    children = manager.get_all_children("chapter")
    assert "section" in children
    assert "subsection" in children
    assert "subsubsection" in children


def test_counter_formatting():
    registers = TexRegisters()
    manager = CounterManager(registers)

    manager.new_counter("test")
    manager.set_counter("test", 12)

    assert manager.get_counter_as_format("test", CounterFormat.ARABIC) == "12"
    assert manager.get_counter_as_format("test", CounterFormat.ROMAN) == "xii"
    assert manager.get_counter_as_format("test", CounterFormat.ROMAN_UPPER) == "XII"
    assert manager.get_counter_as_format("test", CounterFormat.ALPHA) == "l"
    assert manager.get_counter_as_format("test", CounterFormat.ALPHA_UPPER) == "L"

    # test hierarchy formatting
    manager.set_counter("section", 1)
    manager.set_counter("subsection", 3)
    assert (
        manager.get_counter_as_format("subsection", CounterFormat.ARABIC, True) == "1.3"
    )
    assert (
        manager.get_counter_as_format("subsection", CounterFormat.ROMAN, True)
        == "i.iii"
    )


def test_counter_within():
    registers = TexRegisters()
    manager = CounterManager(registers)

    # Create test counters
    manager.new_counter("parent1")
    manager.new_counter("parent2")
    manager.new_counter("child")

    # Test making child subordinate to parent1
    manager.counter_within("child", "parent1")
    assert "child" in manager.get_all_children("parent1")
    assert manager.get_counter_hierarchy("child") == ["parent1", "child"]

    # Test moving child to parent2
    manager.counter_within("child", "parent2")
    assert "child" not in manager.get_all_children("parent1")
    assert "child" in manager.get_all_children("parent2")
    assert manager.get_counter_hierarchy("child") == ["parent2", "child"]

    # Test removing parent relationship
    manager.counter_within("child", None)
    assert "child" not in manager.get_all_children("parent2")
    assert manager.get_counter_hierarchy("child") == ["child"]

    # Test counter resetting behavior
    manager.counter_within("child", "parent1")
    manager.set_counter("child", 5)
    manager.step_counter("parent1")
    assert manager.get_counter_value("child") == 0

    # Test error cases
    manager.counter_within("nonexistent", "parent1")  # Should log warning
    manager.counter_within("child", "nonexistent")  # Should log warning
