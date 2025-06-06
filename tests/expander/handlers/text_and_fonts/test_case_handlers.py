import pytest
from latex2json.expander.expander import Expander
from tests.test_utils import assert_token_sequence


def test_case_handlers():
    expander = Expander()

    # Test basic uppercase and lowercase
    assert_token_sequence(
        expander.expand(r"\uppercase{hello}"), expander.expand("HELLO")
    )
    assert_token_sequence(
        expander.expand(r"\lowercase{WORLD}"), expander.expand("world")
    )

    # Test with macro definitions
    expander.expand(r"\def\foo{foo}")

    # Test that macros are not expanded inside case transforms
    assert_token_sequence(
        expander.expand(r"\uppercase{\foo bar}"), expander.expand("foo BAR")
    )

    # Test with \expandafter to force macro expansion
    assert_token_sequence(
        expander.expand(r"\uppercase\expandafter{\foo bar}"), expander.expand("FOO BAR")
    )

    # Test with multiple words and spaces
    assert_token_sequence(
        expander.expand(r"\uppercase{hello world}"), expander.expand("HELLO WORLD")
    )
    assert_token_sequence(
        expander.expand(r"\lowercase{HELLO WORLD}"), expander.expand("hello world")
    )

    # Test with mixed case input
    assert_token_sequence(
        expander.expand(r"\uppercase{HeLLo WoRLD}"), expander.expand("HELLO WORLD")
    )
    assert_token_sequence(
        expander.expand(r"\lowercase{HeLLo WoRLD}"), expander.expand("hello world")
    )

    # Test error cases
    assert expander.expand(r"\uppercase") == []  # No argument
    assert expander.expand(r"\lowercase") == []  # No argument

    # Test with non-letter tokens (should remain unchanged)
    assert_token_sequence(
        expander.expand(r"\uppercase{123 aa @}"), expander.expand("123 AA @")
    )
    assert_token_sequence(
        expander.expand(r"\lowercase{123 AA @}"), expander.expand("123 aa @")
    )

    # Test nested case transforms
    assert_token_sequence(
        expander.expand(r"\uppercase{Hey \lowercase{HELLO} bud}"),
        expander.expand("HEY hello BUD"),  # lowercase applied last, thus HELLO->hello
    )
