import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_tokens_startwith, assert_tokens_endwith


def test_ifdim_handler():
    expander = Expander()

    # Test basic dimension comparisons
    test_less_than = r"""
    \ifdim 1pt < 2pt
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_equal = r"""
    \ifdim 2pt = 2pt
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_greater_than = r"""
    \ifdim 3pt > 2pt
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_false_less = r"""
    \ifdim 2pt < 1pt
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_false_equal = r"""
    \ifdim 1pt = 2pt
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_false_greater = r"""
    \ifdim 1pt > 2pt
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


def test_ifdim_handler_with_registers():
    expander = Expander()

    # Test with dimen registers
    test_with_registers = r"""
    \dimen0=5pt
    \dimen1=3pt
    \ifdim\dimen0>\dimen1
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_with_mixed = r"""
    \dimen0=5in
    \ifdim \dimen0 = 5in
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    pairs = [
        [test_with_registers, "TRUE"],
        [test_with_mixed, "TRUE"],
    ]

    for test, expected in pairs:
        out1 = strip_whitespace_tokens(expander.expand(test))
        out2 = strip_whitespace_tokens(expander.expand(expected))
        assert Expander.check_tokens_equal(out1, out2)


def test_ifdim_handler_with_macros():
    expander = Expander()

    # Test with macro expansion
    test_with_macros = r"""
    \def\foo{5pt}
    \def\bar{3pt}
    \ifdim\foo>\bar
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_with_macros_false = r"""
    \def\foo{5pt}
    \def\bar{3pt}
    \ifdim\foo<\bar
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_with_mixed_macro = r"""
    \def\foo{5pt}
    \ifdim\foo=10pt
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


def test_ifdim_handler_errors():
    expander = Expander()

    # Test invalid syntax
    invalid_cases = [
        r"\ifdim",  # Missing dimensions
        r"\ifdim 1pt",  # Missing operator and second dimension
        r"\ifdim 1pt ?",  # Invalid operator
        r"\ifdim 1pt < ",  # Missing second dimension
    ]

    for test in invalid_cases:
        out = strip_whitespace_tokens(expander.expand(test))
        # Should return empty list for invalid cases
        assert len(out) == 0


def test_nested_ifdim():
    expander = Expander()

    test_nested = r"""
    \dimen0=5pt
    \dimen1=3pt
    \ifdim\dimen0>\dimen1
        TRUE
        \ifdim \dimen0 < 2pt
            INNER TRUE
        \else
            INNER FALSE
        \fi
    \else
        FALSE
        
    \fi
    """.strip()

    out = expander.expand(test_nested)
    out = strip_whitespace_tokens(out)
    assert_tokens_startwith(out, expander.expand("TRUE"))
    assert_tokens_endwith(out, expander.expand("INNER FALSE"))

    # test inline conditionals

    text = r"""
    \newdimen\mydim
    \mydim=800pt
    \newdimen\maxdimen
    \maxdimen=1000pt

    \ifdim\ifdim\mydim>615pt\mydim\else\maxdimen\fi<650pt\relax
    in range%
    \else
    out of range%
    \fi
    """

    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert expander.check_tokens_equal(out, expander.expand("out of range"))
