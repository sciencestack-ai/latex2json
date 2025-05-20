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
    assert_token_sequence(out, expander.expand("BEGIN ABC 123CONTENTEND"))


def test_begin_end_with_arguments():
    expander = Expander()

    # Environment with one required argument
    expander.expand(r"\newenvironment{boxed}[1]{#1:}{!}")

    out = expander.expand(r"\begin{boxed}{Hello}World\end{boxed}")
    assert_token_sequence(out, expander.expand("Hello:World!"))

    # Environment with optional and required arguments
    expander.expand(r"\newenvironment{fancy}[2][*]{#1-#2:}{.}")

    out = expander.expand(r"\begin{fancy}[+]{Text}Content\end{fancy}")
    assert_token_sequence(out, expander.expand("+-Text:Content."))

    # Using default optional argument
    out = expander.expand(r"\begin{fancy}{Text}Content\end{fancy}")
    assert_token_sequence(out, expander.expand("*-Text:Content."))


def test_nested_environments():
    expander = Expander()

    expander.expand(r"\newenvironment{outer}{<}{>}")
    expander.expand(r"\newenvironment{inner}{[}{]}")

    out = expander.expand(r"\begin{outer}A\begin{inner}B\end{inner}C\end{outer}")
    assert_token_sequence(out, expander.expand("<A[B]C>"))


def test_error_cases():
    expander = Expander()

    # Test undefined environment
    # we return the raw tokens for undefined environments
    out = expander.expand(r"\begin{undefined}content\end{undefined}")
    expected = [
        Token(TokenType.CONTROL_SEQUENCE, "begin"),
        BEGIN_BRACE_TOKEN,
        *expander.expand("undefined"),
        END_BRACE_TOKEN,
        *expander.expand("content"),
        Token(TokenType.CONTROL_SEQUENCE, "end"),
        BEGIN_BRACE_TOKEN,
        *expander.expand("undefined"),
        END_BRACE_TOKEN,
    ]
    assert_token_sequence(out, expected)

    # Test mismatched begin/end
    expander.expand(r"\newenvironment{test}{START}{END}")
    out = expander.expand(r"\begin{test}content\end{wrong}")
    # Should return raw tokens for end{wrong} since it is undefined
    assert_token_sequence(out, expander.expand(r"STARTcontent\end{wrong}"))


def test_environment_without_content():
    expander = Expander()

    expander.expand(r"\renewenvironment{empty}{START}{END}")

    # Test environment with no content
    out = expander.expand(r"\begin{empty}\end{empty}")
    assert_token_sequence(out, expander.expand("STARTEND"))


def test_environment_with_special_characters():
    expander = Expander()

    # Environment containing special LaTeX characters
    expander.expand(r"\newenvironment{math}{$}{$}")

    out = expander.expand(r"\begin{math}x^2\end{math}")
    assert_token_sequence(out, expander.expand("$x^2$"))


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
