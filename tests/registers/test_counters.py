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

    manager.new_counter("subchild", parent="child")
    manager.set_counter("subchild", 10)
    assert manager.get_counter_value("subchild") == 10

    # Test stepping counter (should reset children recursively)
    manager.step_counter("mycounter")
    assert manager.get_counter_value("mycounter") == 43
    assert manager.get_counter_value("child") == 0
    assert manager.get_counter_value("subchild") == 0

    manager.add_to_counter("mycounter", -3)
    assert manager.get_counter_value("mycounter") == 40


def test_counter_hierarchy():
    registers = TexRegisters()
    manager = CounterManager(registers)

    # Test getting all children
    children = manager.get_all_children("chapter")
    assert "section" in children
    assert "subsection" in children
    assert "subsubsection" in children

    # check hierarchy output
    manager.step_counter("part")
    assert manager.get_counter_display("part") == "I"
    manager.step_counter("chapter")
    assert manager.get_counter_display("chapter") == "1"
    manager.step_counter("section")
    assert manager.get_counter_display("section") == "1.1"
    manager.step_counter("subsection")
    assert manager.get_counter_display("subsection") == "1.1.1"

    manager.step_counter("chapter")
    assert manager.get_counter_display("chapter") == "2"
    manager.step_counter("section")
    assert manager.get_counter_display("section") == "2.1"

    # now reset
    manager.reset_section_counters()
    manager.step_counter("part")
    assert manager.get_counter_display("part") == "I"

    # now check that because chapter is 0, section becomes default "1"
    assert manager.get_counter_value("chapter") == 0
    manager.step_counter("section")
    assert manager.get_counter_display("section") == "1"


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
