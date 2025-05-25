from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.registers.counter_handlers import (
    register_counter_handlers,
)


def test_basic_counter_operations():
    expander = ExpanderCore()
    register_counter_handlers(expander)

    # Test setcounter
    expander.expand(r"\setcounter{section}{10}")
    assert expander.state.get_counter_value("section") == 10

    # Test addtocounter
    expander.expand(r"\addtocounter{section}{5}")
    assert expander.state.get_counter_value("section") == 15

    # Test stepcounter
    expander.expand(r"\stepcounter{section}")
    assert expander.state.get_counter_value("section") == 16

    # Test refstepcounter (should behave same as stepcounter)
    expander.expand(r"\refstepcounter{section}")
    assert expander.state.get_counter_value("section") == 17

    # Test value command
    out = expander.expand(r"\value{section}")
    assert expander.convert_tokens_to_str(out) == "17"

    # test parent-child relationship and reset with stepcounter/refstepcounter
    expander.expand(r"\refstepcounter{subsection}")
    assert expander.state.get_counter_value("subsection") == 1

    expander.expand(r"\refstepcounter{section}")
    assert expander.state.get_counter_value("section") == 18
    assert expander.state.get_counter_value("subsection") == 0


def test_new_counter():
    expander = ExpanderCore()
    register_counter_handlers(expander)

    # Test counter with parent
    expander.expand(r"\newcounter{mycounter}[section]")
    assert expander.state.get_counter_value("mycounter") == 0

    # Set values and verify parent-child relationship
    expander.expand(r"\setcounter{mycounter}{10}")
    assert expander.state.get_counter_value("mycounter") == 10

    # Stepping parent should reset child
    expander.expand(r"\stepcounter{section}")
    assert expander.state.get_counter_value("mycounter") == 0


def test_counter_the_command():
    expander = ExpanderCore()
    register_counter_handlers(expander)

    # Create counter and test \the<counter> command
    expander.expand(r"\newcounter{mycounter}")
    expander.expand(r"\setcounter{mycounter}{42}")

    out = expander.expand(r"\themycounter")
    assert expander.convert_tokens_to_str(out) == "42"


def test_counter_error_cases():
    expander = ExpanderCore()
    register_counter_handlers(expander)

    # Test missing counter name
    out = expander.expand(r"\setcounter{}")
    assert out == []

    # Test missing value
    out = expander.expand(r"\setcounter{mycounter}")
    assert out == []

    # Test non-existent counter in \value
    out = expander.expand(r"\value{nonexistent}")
    assert out == []


def test_counter_scope():
    expander = ExpanderCore()
    register_counter_handlers(expander)

    # Test that counter operations are global (not affected by scope)
    expander.push_scope()
    expander.expand(r"\setcounter{section}{10}")
    expander.pop_scope()

    assert expander.state.get_counter_value("section") == 10
