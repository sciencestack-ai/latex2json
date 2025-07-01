from latex2json.expander.expander import Expander
from latex2json.expander.handlers.registers.counter_format_handlers import (
    register_counter_format_handlers,
)
from latex2json.expander.handlers.registers.counter_handlers import (
    register_counter_handlers,
)


def test_counter_formats():
    expander = Expander()
    register_counter_handlers(expander)
    register_counter_format_handlers(expander)

    # Set up a counter value
    expander.expand(r"\setcounter{section}{4}")

    # Test different formats
    out = expander.expand(r"\roman{section}")
    assert expander.convert_tokens_to_str(out) == "iv"

    out = expander.expand(r"\Roman{section}")
    assert expander.convert_tokens_to_str(out) == "IV"

    out = expander.expand(r"\alph{section}")
    assert expander.convert_tokens_to_str(out) == "d"

    out = expander.expand(r"\Alph{section}")
    assert expander.convert_tokens_to_str(out) == "D"

    out = expander.expand(r"\arabic{section}")
    assert expander.convert_tokens_to_str(out) == "4"

    # test nested e.g. subsection
    expander.expand(r"\setcounter{subsection}{1}")
    out = expander.expand(r"\arabic{subsection}")
    assert expander.convert_tokens_to_str(out) == "1"


def test_format_error_cases():
    expander = Expander()
    register_counter_handlers(expander)
    register_counter_format_handlers(expander)

    # Test missing counter name
    out = expander.expand(r"\roman{}")
    assert out == []

    # Test non-existent counter
    out = expander.expand(r"\roman{nonexistent}")
    assert out == []

    # Test with larger numbers for alph/Alph (should handle gracefully)
    expander.expand(r"\setcounter{section}{27}")  # Beyond 'z'/'Z'
    out = expander.expand(r"\alph{section}")
    assert expander.convert_tokens_to_str(out) == "aa"

    out = expander.expand(r"\Alph{section}")
    assert expander.convert_tokens_to_str(out) == "AA"
