import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_tokens_endwith, assert_tokens_startwith


def test_ifcat_handler():
    expander = Expander()

    # test with two letters

    test_with_aa = r"""
    \ifcat aa
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_with_ab = r"""
    \ifcat ab
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_with_a1 = r"""
    \ifcat a1 % different catcode
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    test_with_11 = r"""
    \ifcat11
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    # space sensitive!
    test_with_letter_and_space = r"""
    \ifcat a 
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    pairs = [
        [test_with_aa, "TRUE"],
        [test_with_ab, "TRUE"],
        [test_with_a1, "FALSE"],
        [test_with_11, "TRUE"],
        [test_with_letter_and_space, "FALSE"],
    ]

    for test, expected in pairs:
        out1 = strip_whitespace_tokens(expander.expand(test))
        out2 = strip_whitespace_tokens(expander.expand(expected))
        assert Expander.check_tokens_equal(out1, out2)


def test_ifcat_handler_with_control_sequences():
    expander = Expander()

    # note that \ifcat EXPANDS then CHECKS the tokens POST EXPANSION
    a_b = r"""
    \def\a{a}
    \def\b{b}
    \ifcat \a\b
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    a_1 = r"""
    \def\a{a}
    \def\b{1}
    \ifcat \a\b
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    a_with_space = r"""
    \def\a{a}
    \ifcat \a 
        TRUE
    \else
        FALSE
    \fi""".strip()

    pairs = [
        [a_b, "TRUE"],
        [a_1, "FALSE"],
        [a_with_space, "FALSE"],
    ]

    for test, expected in pairs:
        out1 = strip_whitespace_tokens(expander.expand(test))
        out2 = strip_whitespace_tokens(expander.expand(expected))
        assert Expander.check_tokens_equal(out1, out2)

    # now it gets more complicated. control sequences with multiple tokens
    text = r"""
    \def\foo{FOO}
    \def\bar{BAR}
    % NOTE THAT \ifcat EXPANDS then CHECKS the tokens POST EXPANSION i.e. \foo->FOO
    % \ifcat checks ['F','O'] = True, then pushes the remaining tokens into the stream
    \ifcat \foo\bar % expands to FOOBAR, 'F' and 'O' are consumed for \ifcat. Left with OBAR
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    out = strip_whitespace_tokens(expander.expand(text))
    assert_tokens_startwith(out, expander.expand("OBAR"))
    assert_tokens_endwith(out, expander.expand("TRUE"))

    text = r"""
    \def\foo{F1O}
    % NOTE THAT \ifcat EXPANDS then CHECKS the tokens POST EXPANSION i.e. \foo->F1O
    % \ifcat checks ['F','1'] = FALSE, then pushes the remaining tokens into the stream
    \ifcat \foo\bar 
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    out = strip_whitespace_tokens(expander.expand(text))
    assert Expander.check_tokens_equal(out, expander.expand("FALSE"))
