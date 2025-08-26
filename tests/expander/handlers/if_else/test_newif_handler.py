import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_newif_basic():
    expander = Expander()

    # Test basic true/false cases
    test_false_default = r"""
    \newif\iftest
    \iftest
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_explicit_false = r"""
    \newif\iftest
    \testfalse
    \iftest
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_true = r"""
    \newif\iftest
    \testtrue
    \iftest
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    pairs = [
        [test_false_default, "FALSE"],  # Default is false
        [test_explicit_false, "FALSE"],
        [test_true, "TRUE"],
    ]

    for test, expected in pairs:
        out1 = strip_whitespace_tokens(expander.expand(test))
        out2 = strip_whitespace_tokens(expander.expand(expected))
        assert Expander.check_tokens_equal(out1, out2)

    assert expander.check_macro_is_user_defined("iftest")


def test_newif_nested():
    expander = Expander()

    test_nested = r"""
    \newif\ifouter
    \newif\ifinner
    \outertrue
    \innertrue
    \ifouter
        \ifinner
            BOTH_TRUE
        \else
            OUTER_ONLY
        \fi
    \else
        \ifinner
            INNER_ONLY
        \else
            BOTH_FALSE
        \fi
    \fi
    """.strip()

    out = strip_whitespace_tokens(expander.expand(test_nested))
    assert_token_sequence(out, expander.expand("BOTH_TRUE"))

    # Test with different combinations
    test_outer_only = r"""
    \newif\ifouter
    \newif\ifinner
    \outertrue
    \innerfalse
    \ifouter
        \ifinner
            BOTH_TRUE
        \else
            OUTER_ONLY
        \fi
    \fi
    """.strip()

    out = strip_whitespace_tokens(expander.expand(test_outer_only))
    assert_token_sequence(out, expander.expand("OUTER_ONLY"))


def test_newif_errors():
    expander = Expander()

    # Test invalid syntax cases
    invalid_cases = [
        r"\newif",  # Missing name
        r"\newif\test",  # Name doesn't start with if
        r"\newif\if",  # Empty name after if
    ]

    for test in invalid_cases:
        out = strip_whitespace_tokens(expander.expand(test))
        # Should return empty list for invalid cases
        assert len(out) == 0


def test_newif_persistence():
    expander = Expander()

    # Test that condition state persists
    test_persistence = r"""
    \newif\iftest
    \testtrue
    \testfalse
    \testtrue
    \iftest
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    out = strip_whitespace_tokens(expander.expand(test_persistence))
    assert_token_sequence(out, expander.expand("TRUE"))


def test_newif_global_scope():
    expander = Expander()

    # Test that newif definitions are global
    test_global = r"""
    {
        \newif\ifglobal
        \globaltrue
    }
    """.strip()
    expander.expand(test_global)

    test_global_check = r"""
    \ifglobal
        STILL_TRUE
    \else
        NOT_TRUE
    \fi
    """.strip()

    out = strip_whitespace_tokens(expander.expand(test_global_check))
    assert_token_sequence(out, expander.expand("STILL_TRUE"))


def test_newif_redefinition():
    expander = Expander()

    # Test redefining an existing if condition
    test_redef = r"""
    \newif\iftest
    \testtrue
    \newif\iftest  % Redefining should reset to false
    \iftest
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    out = strip_whitespace_tokens(expander.expand(test_redef))
    assert_token_sequence(out, expander.expand("FALSE"))


def test_newif_internals():
    expander = Expander()

    test_internals = r"""
    \makeatletter
    \@ignoretrue
    \if@ignore
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    out = strip_whitespace_tokens(expander.expand(test_internals))
    assert_token_sequence(out, expander.expand("TRUE"))
