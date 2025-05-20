import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_tokens_endwith, assert_tokens_startwith


def test_ifx_simple_same_tokens():
    expander = Expander()
    text = r"""
    \def\a{Hello}
    \def\b{Hello}
    \ifx\a\b
        Tokens are the same
    \else
        Tokens are different
    \fi
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    expected = expander.expand("Tokens are the same")
    assert Expander.check_tokens_equal(out, expected)

    # test single characters
    text = r"""
    \ifx aa
        SAME
    \else
        DIFFERENT
    \fi
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    expected = expander.expand("SAME")
    assert Expander.check_tokens_equal(out, expected)


def test_ifx_simple_different_tokens():
    expander = Expander()
    text = r"""
    \def\a{Hello}
    \def\b{World}
    \ifx\a\b
        Tokens are the same
    \else
        Tokens are different
    \fi
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    expected = expander.expand("Tokens are different")
    expected = strip_whitespace_tokens(expected)
    assert Expander.check_tokens_equal(out, expected)

    text = r"""
    \def\x{x}
    \ifx \x x 
        SAME
    \else
        DIFFERENT
    \fi
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    expected = expander.expand("DIFFERENT")
    assert Expander.check_tokens_equal(out, expected)

    # test single characters
    text = r"""
    \ifx a b 
        SAME
    \else
        DIFFERENT
    \fi
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    expected = expander.expand("DIFFERENT")
    assert Expander.check_tokens_equal(out, expected)


def test_ifx_control_sequences_same_definition():
    expander = Expander()
    text = r"""
    \def\foo{BAR}
    \def\a{\foo}
    \def\b{\foo}
    \ifx\a\b
        Control sequences are the same
    \else
        Control sequences are different
    \fi
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    expected = expander.expand("Control sequences are the same")
    expected = strip_whitespace_tokens(expected)
    assert Expander.check_tokens_equal(out, expected)


def test_ifx_control_sequences_different_definition():
    expander = Expander()
    text = r"""
    \def\foo{BAR}
    \def\baz{QUX}
    \def\a{\foo}
    \def\b{\baz}
    \ifx\a\b
        Control sequences are the same
    \else
        Control sequences are different
    \fi
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    expected = expander.expand("Control sequences are different")
    expected = strip_whitespace_tokens(expected)
    assert Expander.check_tokens_equal(out, expected)


def test_ifx_nested():
    expander = Expander()
    text = r"""
    \def\foo{FOO}
    \def\a{\foo}
    \def\b{\foo}
    \def\c{BAR}
    \def\d{BAR}

    \ifx \a \c
        OUTER SAME
        \ifx\a\c
            INNER SAME AC
        \else
            INNER DIFFERENT AC
        \fi
    \else
        OUTER DIFFERENT
        \ifx\b \d
            INNER SAME BD
        \else
            INNER DIFFERENT BD
        \fi
    \fi
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert_tokens_startwith(out, expander.expand("OUTER DIFFERENT"))
    assert_tokens_endwith(out, expander.expand("INNER DIFFERENT BD"))


def test_ifx_no_tokens_after_ifx():
    expander = Expander()
    text = r"\def\a{A}\def\b{A}\ifx\a\b"  # Missing content and \fi
    # This should not raise an error during check_ifx_equals,
    # but process_if_else_block might log a warning or return None/empty.
    # The current implementation of process_if_else_block expects further tokens.
    # We are testing that check_ifx_equals handles this gracefully.
    # The ifx_handler itself will log a warning if no tokens follow the condition.
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert len(out) == 0  # Expecting nothing as the block is incomplete


def test_ifx_missing_second_token():
    expander = Expander()
    text = r"\def\a{A}\ifx\a"  # Missing second token and content
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert len(out) == 0


def test_ifx_missing_first_token():
    expander = Expander()
    # This case is tricky because \ifx itself is a token.
    # The parser would expect a token after \ifx.
    # If \ifx is followed immediately by EOF or another \ifx, it's an issue.
    text = r"\ifx "  # Whitespace is skipped, then expects a token
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert len(out) == 0


def test_ifx_with_undefined_macros():
    expander = Expander()
    text = r"""
    \ifx\undefinedmacroA\undefinedmacroB
        SAME
    \else
        DIFFERENT
    \fi
    """.strip()
    # Undefined macros are treated as specific command tokens.
    # If they are the same command token, they are "equal" for \ifx.
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    expected = expander.expand(
        "SAME"
    )  # Since \undefinedmacroA is token-equal to \undefinedmacroB
    expected = strip_whitespace_tokens(expected)
    assert Expander.check_tokens_equal(out, expected)


def test_ifx_with_one_undefined_one_defined_macro():
    expander = Expander()
    text = r"""
    \def\aaa{\xxx}
    \ifx \aaa \xxx
        SAME
    \else
        DIFFERENT
    \fi
    """.strip()
    # \undefinedmacroA (a command token) vs \definedmacro (which expands to "DEF")
    # Their definitions are different.
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    expected = expander.expand("DIFFERENT")
    expected = strip_whitespace_tokens(expected)
    assert Expander.check_tokens_equal(out, expected)
