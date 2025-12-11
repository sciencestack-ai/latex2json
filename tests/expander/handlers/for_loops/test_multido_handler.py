import pytest

from latex2json.expander.expander import Expander
from latex2json.expander.handlers.for_loops.multido_handler import (
    register_multido_handler,
)
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_multido_basic_integer():
    """Test multido with basic integer iteration"""
    expander = Expander()

    text = r"\multido{\I=1+1}{5}{Item \I. }"
    out = expander.expand(text)
    strip_whitespace_tokens(out)

    expected = expander.expand("Item 1. Item 2. Item 3. Item 4. Item 5.")
    assert_token_sequence(out, expected)


def test_multido_with_includegraphics_example():
    """Test multido with the original example from the user"""
    expander = Expander()

    # Simulate the original use case
    text = r"\multido{\I=1+1}{6}{\I }"
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    # Should produce: 1 2 3 4 5 6
    assert out_str.replace(" ", "") == "123456"


def test_multido_decimal_values():
    """Test multido with decimal increments"""
    expander = Expander()

    text = r"\multido{\n=0.0+0.5}{5}{[\n]}"
    out = expander.expand(text)
    strip_whitespace_tokens(out)

    expected = expander.expand("[0][0.5][1][1.5][2]")
    assert_token_sequence(out, expected)


def test_multido_negative_increment():
    """Test multido with negative increment (countdown)"""
    expander = Expander()

    text = r"\multido{\I=5-1}{5}{\I }"
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    # Should count down: 5, 4, 3, 2, 1
    assert "5" in out_str and "4" in out_str and "1" in out_str


def test_multido_multiple_variables():
    """Test multido with multiple variables"""
    expander = Expander()

    text = r"\multido{\I=1+1,\n=0.0+0.2}{5}{\I:\n }"
    out = expander.expand(text)
    strip_whitespace_tokens(out)

    expected = expander.expand("1:0 2:0.2 3:0.4 4:0.6 5:0.8")
    assert_token_sequence(out, expected)


def test_multido_zero_repetitions():
    """Test multido with zero repetitions"""
    expander = Expander()

    text = r"\multido{\I=1+1}{0}{Should not appear}"
    out = expander.expand(text)
    assert out == []


def test_multido_negative_repetitions():
    """Test multido with negative repetitions (should not iterate)"""
    expander = Expander()

    text = r"\multido{\I=1+1}{-5}{Should not appear}"
    out = expander.expand(text)
    assert out == []


def test_multido_variable_scoping():
    """Test that multido variables don't leak outside the loop"""
    expander = Expander()

    # Define a macro with same name as multido variable
    expander.expand(r"\newcommand{\I}{ORIGINAL}")

    text = r"\multido{\I=1+1}{3}{\I} \I"
    out = expander.expand(text)
    strip_whitespace_tokens(out)

    # The multido should use its own variable, then revert to original
    expected = expander.expand("123 ORIGINAL")
    assert_token_sequence(out, expected)


def test_multido_with_macro_in_body():
    """Test multido with macro expansion in body"""
    expander = Expander()

    text = r"""
    \def\item#1{[#1]}
    \multido{\I=1+1}{3}{%
        \item{\I}
    }"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_str = out_str.replace("\n", "").replace(" ", "")
    assert out_str == "[1][2][3]"


def test_multido_starting_from_zero():
    """Test multido starting from 0"""
    expander = Expander()

    text = r"\multido{\I=0+1}{4}{\I}"
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert "0" in out_str and "1" in out_str and "2" in out_str and "3" in out_str


def test_multido_large_increment():
    """Test multido with large increment"""
    expander = Expander()

    text = r"\multido{\I=0+10}{4}{\I }"
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    # Should produce: 0, 10, 20, 30
    assert "0" in out_str and "10" in out_str and "20" in out_str and "30" in out_str


def test_multido_single_iteration():
    """Test multido with single iteration"""
    expander = Expander()

    text = r"\multido{\I=42+1}{1}{Value: \I}"
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert "42" in out_str


def test_multido_negative_start_value():
    """Test multido with negative start value"""
    expander = Expander()

    text = r"\multido{\I=-2+1}{5}{\I }"
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    # Should produce: -2, -1, 0, 1, 2
    assert "-2" in out_str and "-1" in out_str and "0" in out_str
