import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import (
    EnvironmentEndToken,
    EnvironmentStartToken,
    Token,
    TokenType,
)
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.expander.handlers.sectioning.test_section_handlers import mock_section_token
from tests.test_utils import assert_token_sequence


def test_basic_begin_end():
    expander = Expander()

    # Define a simple environment
    expander.expand(r"\newenvironment{test}[1]{BEGIN #1 123}{END}")

    # Test basic usage
    out = expander.expand(r"\begin{test}{ABC}CONTENT\end{test}")
    assert_token_sequence(out, expander.expand(r"\test{ABC}CONTENT\endtest"))

    expected = [
        EnvironmentStartToken("test"),
        *expander.expand("BEGIN ABC 123CONTENTEND"),
        EnvironmentEndToken("test"),
    ]
    assert_token_sequence(out, expected)


def test_nested_environments():
    expander = Expander()

    expander.expand(r"\newenvironment{outer}{<}{>}")
    expander.expand(r"\newenvironment{inner}{[}{]}")

    out = expander.expand(r"\begin{outer}A\begin{inner}B\end{inner}C\end{outer}")
    expected = [
        EnvironmentStartToken("outer"),
        *expander.expand("<A"),
        EnvironmentStartToken("inner"),
        *expander.expand("[B]"),
        EnvironmentEndToken("inner"),
        *expander.expand("C>"),
        EnvironmentEndToken("outer"),
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
        EnvironmentStartToken("test"),
        *expander.expand("START"),
        *expander.expand("CONTENT"),
        *expander.expand("END"),
        EnvironmentEndToken("test"),
    ]
    assert_token_sequence(out, expected)

    # Test nested csname with environment name
    expander.expand(r"\def\envname{test}")
    out = expander.expand(
        r"\begin{\csname envname\endcsname}CONTENT\end{\csname envname\endcsname}"
    )
    assert_token_sequence(out, expected)


def test_begin_end_default_to_macro():
    expander = Expander()

    text = r"""
    % \begin{section} is not defined, so it should expand to to \section but wrapped in \begin{section} block as well
    \begin{section}{Intro} \label{sec:intro}
    x = 1
    \end{section}
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out[0] == EnvironmentStartToken("section")
    # second token is the numbered section
    assert out[1] == mock_section_token(expander, "section", "Intro", numbering="1")[0]
    assert out[-1] == EnvironmentEndToken("section")


def test_begin_end_current_env_stacks():
    expander = Expander()

    expander.expand(r"\makeatletter")
    expander.expand(r"\begin{figure}")
    assert expander.get_env_stack() == ["figure"]
    expander.expand(r"\begin{table}")
    assert expander.get_env_stack() == ["figure", "table"]

    # also test with @float
    expander.expand(r"\@float{table}")
    assert expander.get_env_stack() == ["figure", "table", "table"]
    expander.expand(r"\end@float")
    assert expander.get_env_stack() == ["figure", "table"]

    # test drop \end
    expander.expand(r"\end{figure}")
    assert expander.get_env_stack() == []
    # expander.expand(r"\end{figure}")
    # assert expander.state.get_env_stack() == []
