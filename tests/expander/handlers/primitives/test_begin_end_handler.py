import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_basic_begin_end():
    expander = Expander()

    # Define a simple environment
    expander.expand(r"\newenvironment{test}[1]{BEGIN #1 123}{END}")

    # Test basic usage
    out = expander.expand(r"\begin{test}{ABC}CONTENT\end{test}")
    assert_token_sequence(out, expander.expand(r"\test{ABC}CONTENT\endtest"))

    expected = [
        Token(TokenType.ENVIRONMENT_START, "test"),
        *expander.expand("BEGIN ABC 123CONTENTEND"),
        Token(TokenType.ENVIRONMENT_END, "test"),
    ]
    assert_token_sequence(out, expected)


def test_nested_environments():
    expander = Expander()

    expander.expand(r"\newenvironment{outer}{<}{>}")
    expander.expand(r"\newenvironment{inner}{[}{]}")

    out = expander.expand(r"\begin{outer}A\begin{inner}B\end{inner}C\end{outer}")
    expected = [
        Token(TokenType.ENVIRONMENT_START, "outer"),
        *expander.expand("<A"),
        Token(TokenType.ENVIRONMENT_START, "inner"),
        *expander.expand("[B]"),
        Token(TokenType.ENVIRONMENT_END, "inner"),
        *expander.expand("C>"),
        Token(TokenType.ENVIRONMENT_END, "outer"),
    ]
    assert_token_sequence(out, expected)


def test_that_begin_end_is_scoped():
    expander = Expander()

    assert expander.get_catcode(ord("@")) == 12

    expander.expand(r"\newenvironment{test}{BEGIN}{END}")
    expander.expand(r"\begin{test}")

    # in scope

    # requires catcode handler to be registered
    new_catcode = 11
    catcode_change_text = rf"""
    \catcode`\@={new_catcode}
    """
    expander.expand(catcode_change_text)

    assert expander.get_catcode(ord("@")) == new_catcode

    expander.expand(r"\def\foo{FOO}")
    assert expander.get_macro("\\foo")

    # end test exits scope
    expander.expand(r"\end{test}")

    # back to original
    assert expander.get_catcode(ord("@")) == 12
    assert not expander.get_macro("\\foo")


def test_scope_undefined_environment():
    expander = Expander()

    text = r"""
    \begin{undefined}
    \catcode`\@=11
    \def\foo{FOO}
    \gdef\bar{BAR}
    \global\def\baz{BAZ}
    \end{undefined}
    """
    expander.expand(text)
    assert not expander.get_macro("\\undefined")

    # unaffected since scoped
    assert expander.get_catcode(ord("@")) == 12
    assert not expander.get_macro("\\foo")
    assert expander.get_macro("\\bar")  # since global
    assert expander.get_macro("\\baz")  # since global


def test_begin_end_with_csname():
    expander = Expander()

    # Define an environment
    expander.expand(r"\newenvironment{test}{START}{END}")

    # Test using csname to create begin/end tokens
    out = expander.expand(
        r"\csname begin\endcsname{test}CONTENT\csname end\endcsname{test}"
    )

    expected = [
        Token(TokenType.ENVIRONMENT_START, "test"),
        *expander.expand("START"),
        *expander.expand("CONTENT"),
        *expander.expand("END"),
        Token(TokenType.ENVIRONMENT_END, "test"),
    ]
    assert_token_sequence(out, expected)

    # Test nested csname with environment name
    expander.expand(r"\def\envname{test}")
    out = expander.expand(
        r"\begin{\csname envname\endcsname}CONTENT\end{\csname envname\endcsname}"
    )
    assert_token_sequence(out, expected)
