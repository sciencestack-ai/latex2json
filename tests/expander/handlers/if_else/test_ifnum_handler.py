import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import (
    assert_token_sequence,
    assert_tokens_startwith,
    assert_tokens_endwith,
)


def test_ifnum_handler():
    expander = Expander()

    # Test basic number comparisons
    test_less_than = r"""
    \ifnum 1 < 2
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_equal = r"""
    \ifnum 2 = 2
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_greater_than = r"""
    \ifnum 3 > 2
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_false_less = r"""
    \ifnum 2 < 1
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_false_equal = r"""
    \ifnum 1 = 2
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_false_greater = r"""
    \ifnum 1 > 2
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    pairs = [
        [test_less_than, "TRUE"],
        [test_equal, "TRUE"],
        [test_greater_than, "TRUE"],
        [test_false_less, "FALSE"],
        [test_false_equal, "FALSE"],
        [test_false_greater, "FALSE"],
    ]

    for test, expected in pairs:
        out1 = strip_whitespace_tokens(expander.expand(test))
        out2 = strip_whitespace_tokens(expander.expand(expected))
        assert Expander.check_tokens_equal(out1, out2)


def test_ifnum_handler_with_registers():
    expander = Expander()

    # Test with count registers
    test_with_registers = r"""
    \count0=5
    \count1=3
    \ifnum\count0>\count1
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_with_mixed = r"""
    \count0=5
    \ifnum \count0 =  51
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    pairs = [
        [test_with_registers, "TRUE"],
        [test_with_mixed, "FALSE"],
    ]

    for test, expected in pairs:
        out1 = strip_whitespace_tokens(expander.expand(test))
        out2 = strip_whitespace_tokens(expander.expand(expected))
        assert Expander.check_tokens_equal(out1, out2)


def test_ifnum_handler_with_macros():
    expander = Expander()

    # Test with macro expansion
    test_with_macros = r"""
    \def\foo{5}
    \def\bar{3}
    \ifnum\foo>\bar
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_with_macros_false = r"""
    \def\foo{5}
    \def\bar{3}
    \ifnum\foo<\bar
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_with_mixed_macro = r"""
    \def\foo{5}
    \ifnum\foo=10
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    pairs = [
        [test_with_macros, "TRUE"],
        [test_with_macros_false, "FALSE"],
        [test_with_mixed_macro, "FALSE"],
    ]

    for test, expected in pairs:
        out1 = strip_whitespace_tokens(expander.expand(test))
        out2 = strip_whitespace_tokens(expander.expand(expected))
        assert Expander.check_tokens_equal(out1, out2)


def test_ifnum_handler_errors():
    expander = Expander()

    # Test invalid syntax
    invalid_cases = [
        r"\ifnum",  # Missing numbers
        r"\ifnum 1",  # Missing operator and second number
        r"\ifnum 1 ?",  # Invalid operator
        r"\ifnum 1 < ",  # Missing second number
    ]

    for test in invalid_cases:
        out = strip_whitespace_tokens(expander.expand(test))
        # Should return empty list for invalid cases
        assert len(out) == 0


def test_nested_ifnum():
    expander = Expander()

    # inline conditionals
    out = expander.expand(r"\ifnum\ifnum 1 > 0 1 \else 0 \fi > 0 TRUE \else FALSE \fi")
    out = strip_whitespace_tokens(out)
    assert_token_sequence(out, expander.expand("TRUE"))

    # classic nested
    test_nested = r"""
    \ifnum 1 > 0
        \ifnum 1 > 0 
            TRUE
        \else
            FALSE
        \fi
    \fi
    """.strip()
    out = expander.expand(test_nested)
    out = strip_whitespace_tokens(out)
    assert_token_sequence(out, expander.expand("TRUE"))


def test_with_value():
    text = r"""
    \ifnum\value{page}>10
        A
    \else
        B
    \fi
    """.strip()
    expander = Expander()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert_token_sequence(out, expander.expand("B"))

    expander.expand(r"\setcounter{page}{11}")
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert_token_sequence(out, expander.expand("A"))
