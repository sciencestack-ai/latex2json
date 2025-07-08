import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_basic_newcommand():
    expander = Expander()

    # Basic command without arguments
    text = r"""
    \newcommand{\hello}{Hello, world!}
    """.strip()
    expander.expand(text)
    assert expander.get_macro("\\hello")
    assert_token_sequence(expander.expand(r"\hello"), expander.expand("Hello, world!"))

    # Command with arguments
    text = r"""
    \newcommand{\greet}[2]{Hello #2 and #1!}
    """.strip()
    expander.expand(text)
    assert expander.get_macro("\\greet")
    assert_token_sequence(
        expander.expand(r"\greet{Alice}{Bob}"), expander.expand("Hello Bob and Alice!")
    )

    # test single token args
    assert_token_sequence(
        expander.expand(r"\greet12333"), expander.expand("Hello 2 and 1!333")
    )

    assert expander.check_macro_is_user_defined("greet")
    assert expander.check_macro_is_user_defined("\\hello")


def test_newcommand_with_default():
    expander = Expander()

    # Command with default argument
    text = r"""
    \newcommand{\welcome}[1][friend]{Hello, #1!}
    """.strip()
    expander.expand(text)
    assert expander.get_macro("\\welcome")

    # Test with default argument
    assert_token_sequence(
        expander.expand(r"\welcome"), expander.expand("Hello, friend!")
    )

    # Test with [] argument
    assert_token_sequence(
        expander.expand(r"\welcome[Alice]"), expander.expand("Hello, Alice!")
    )

    # note that {} is not a substitute for [] default
    assert_token_sequence(
        expander.expand(r"\welcome{Alice}"), expander.expand("Hello, friend!{Alice}")
    )

    # now test with multiple arguments with defaults
    text = r"""
    \newcommand{\greet}[2][default]{Hello, #1 and #2!}
    """.strip()
    expander.expand(text)
    assert expander.get_macro("\\greet")
    assert_token_sequence(
        expander.expand(r"\greet  {Alice}{Bob}"),
        expander.expand("Hello, default and Alice!{Bob}"),
    )

    # Test with [] argument
    assert_token_sequence(
        expander.expand(r"\greet [Alice] {Bob}"),
        expander.expand("Hello, Alice and Bob!"),
    )

    # test with 3 args
    text = r"""
    \newcommand\bar{BAR}
    \renewcommand{\greet}[3][default]{Hello #1 and #2 and #3!}
    """.strip()
    expander.expand(text)
    assert_token_sequence(
        expander.expand(r"\greet1\bar3"),
        expander.expand("Hello default and 1 and BAR!3"),
    )


def test_newcommand_redefinition():
    expander = Expander()

    # Define command
    text = r"""
    \newcommand{\greeting} {Hello}
    """.strip()
    expander.expand(text)

    # Attempt to redefine with \newcommand should fail silently
    text = r"""
    \newcommand{\greeting}{Hi}
    """.strip()
    expander.expand(text)

    # Original definition should remain
    assert_token_sequence(expander.expand(r"\greeting"), expander.expand("Hello"))

    # Redefine with \renewcommand should work
    text = r"""
    \renewcommand* {\greeting} {Hi}
    """.strip()
    expander.expand(text)
    assert_token_sequence(expander.expand(r"\greeting"), expander.expand("Hi"))


def test_newcommand_scope():
    expander = Expander()

    # Local definition
    text = r"""
    {
        \newcommand{\local}{Local}
    }
    """.strip()
    expander.expand(text)
    # newcommand is global
    assert expander.get_macro("\\local")


def test_newcommand_expansion():
    expander = Expander()

    # Test nested command expansion
    text = r"""
    \newcommand{\inner}{world}
    \newcommand{\outer}{Hello, \inner!}
    """.strip()
    expander.expand(text)
    assert_token_sequence(expander.expand(r"\outer"), expander.expand("Hello, world!"))

    # Test argument expansion
    text = r"""
    \newcommand{\bolder}[1]{\textbf{#1}}
    \newcommand{\greeting}[1]{\bolder{Hello, #1!}}
    """.strip()
    expander.expand(text)
    assert_token_sequence(
        expander.expand(r"\greeting{world}"), expander.expand(r"\textbf{Hello, world!}")
    )


def test_newcommand_errors():
    expander = Expander()

    # Invalid number of arguments
    text = r"""
    \newcommand{\bad}[x]{Error}
    """.strip()
    expander.expand(text)
    assert not expander.get_macro("\\bad")

    # Missing definition
    text = r"""
    \newcommand{\bad}[1]
    """.strip()
    expander.expand(text)
    assert not expander.get_macro("\\bad")

    # Invalid command name
    text = r"""
    \newcommand{bad}{Error}
    """.strip()
    expander.expand(text)
    assert not expander.get_macro("bad")


def test_newcommand_star():
    expander = Expander()

    # Test starred version (typically used for long definitions in LaTeX)
    text = r"""
    \newcommand*{\star}{Star}
    """.strip()
    expander.expand(text)
    assert expander.get_macro("\\star")
    assert_token_sequence(expander.expand(r"\star"), expander.expand("Star"))


def test_nested_newcommands():
    expander = Expander()

    text = r"""
    \newcommand{\outer}[1]{
        \newcommand{\inner}[1]{
            \newcommand{\last}[1]{
                OUTER: #1, INNER: ##1, LAST: ####1
            }
        }
        \inner{INNER}
    }
    """.strip()
    expander.expand(text)
    assert expander.get_macro("\\outer")
    # inner and last not created yet
    assert not expander.get_macro("\\inner")
    assert not expander.get_macro("\\last")

    expander.expand(r"\outer{123}")
    # inner and last created
    assert expander.get_macro("\\inner")
    assert expander.get_macro("\\last")

    out = expander.expand(r"\last{456}")
    strip_whitespace_tokens(out)
    assert_token_sequence(out, expander.expand("OUTER: 123, INNER: INNER, LAST: 456"))
