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

    assert manager.format_counter("test", CounterFormat.ARABIC) == "12"
    assert manager.format_counter("test", CounterFormat.ROMAN) == "xii"
    assert manager.format_counter("test", CounterFormat.ROMAN_UPPER) == "XII"
    assert manager.format_counter("test", CounterFormat.ALPHA) == "l"
    assert manager.format_counter("test", CounterFormat.ALPHA_UPPER) == "L"
