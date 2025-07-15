import pytest

from latex2json.expander.expander import Expander
from latex2json.expander.handlers.for_loops.for_each_handler import (
    register_for_each_handlers,
)
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_foreach_with_spaces():
    """Test foreach handling of spaces in list items"""
    expander = Expander()

    # ensure whitespace is stripped after the comma, but not rstrip
    text = r"\foreach \x in { apple , banana , orange } {[\x]}"
    out = expander.expand(text)
    strip_whitespace_tokens(out)

    expected = expander.expand("[apple ][banana ][orange ]")
    assert_token_sequence(out, expected)


def test_foreach_with_multiple_variables():
    """Test foreach with multiple variables separated by slash"""
    expander = Expander()

    text = r"\foreach \i/\j in {1/2, 3/4, 5/6} {Item \i has value \j. }"
    out = expander.expand(text)
    strip_whitespace_tokens(out)

    expected = expander.expand(
        "Item 1 has value 2. Item 3 has value 4. Item 5 has value 6."
    )
    assert_token_sequence(out, expected)


def test_foreach_empty_list():
    """Test foreach with empty list"""
    expander = Expander()

    text = r"\foreach \x in {} {Should not appear}"
    out = expander.expand(text)
    assert out == []

    # HOWEVER, empty delimited list e.g. {,,,} SHOULD STILL BE HANDLED
    text = r"\foreach \x in {,,,} {Should appear}"
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "Should appear" * 4


def test_foreach_variable_not_used():
    """Test foreach where variable is not used in body"""
    expander = Expander()

    text = r"\foreach \x in {1, 2, 3} {Hello }"
    out = expander.expand(text)
    strip_whitespace_tokens(out)

    expected = expander.expand("Hello Hello Hello")
    assert_token_sequence(out, expected)


def test_foreach_uneven_variable_count():
    """Test foreach with uneven number of variables vs values"""
    expander = Expander()

    # More variables than values - should cycle through available values
    text = r"\foreach \x/\y/\z in {a/b, c/d} {\x-\y-\z }"
    out = expander.expand(text)
    strip_whitespace_tokens(out)

    # First iteration: x=a, y=b, z=a (cycles back)
    # Second iteration: x=c, y=d, z=c (cycles back)
    expected = expander.expand("a-b-a c-d-c")
    assert_token_sequence(out, expected)


def test_foreach_variable_scoping():
    """Test that foreach variables don't interfere with existing macros"""
    expander = Expander()

    # Define a macro with same name as foreach variable
    expander.expand(r"\newcommand{\x}{ORIGINAL}")

    text = r"\foreach \x in {1, 2} {\x} \x"
    out = expander.expand(text)
    strip_whitespace_tokens(out)

    # The foreach should use its own variable, then revert to original
    expected = expander.expand("12 ORIGINAL")
    assert_token_sequence(out, expected)


def test_foreach_expansion():
    expander = Expander()

    text = r"""
    \def\xxx#1{*#1*} % this is done to check that the \item macro is expanded correctly
    \foreach\item in {apple,banana,cherry} {%
        \xxx\item % \item is a macro, so this will be expanded to \xxx\item -> *\item* -> *apple*, and NOT \xxxapple -> *a*pple
    }"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_str = out_str.replace("\n", "").replace(" ", "")
    assert out_str == "*apple**banana**cherry*"
