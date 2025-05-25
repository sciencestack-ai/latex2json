import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_tokens_endwith, assert_tokens_startwith


def test_if_handler():
    expander = Expander()

    # single line asserts
    assert Expander.check_tokens_equal(
        expander.expand(r"\if 11TRUE\fi"), expander.expand("TRUE")
    )
    assert Expander.check_tokens_equal(expander.expand(r"\if ab TRUE \fi"), [])
    assert Expander.check_tokens_equal(
        expander.expand(r"\if abTRUE\else{FALSE}\empty\fi"), expander.expand("{FALSE}")
    )

    text = r"""
    \if aa
        TRUE
    \else
        FALSE
    \fi

    \if b a 
        B==A
    \else
        B!=A
    \fi
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert_tokens_startwith(out, expander.expand("TRUE"))
    assert_tokens_endwith(out, expander.expand("B!=A"))

    text = r"""
    \def\a{aaa}
    \def\b{bbb}
    \if \a\b
        TRUE
    \else
        FALSE
    \fi
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert Expander.check_tokens_equal(out, expander.expand("FALSE"))

    text = r"""
    \def\a{baa} % NOTE THAT \if only checks FIRST token if both are control sequences
    \def\b{bbb}
    \if \a\b  % TRUE
        TRUE 
    \else
        FALSE
    \fi
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert Expander.check_tokens_equal(out, expander.expand("TRUE"))

    # test one control sequence and one letter
    text = r"""
    \def\a{abb}
    \if \a a % FALSE because this checks abb with a
        TRUE
    \else
        FALSE
    \fi
    
    \def\a{a} 
    \if \a a % TRUE because this checks a with a
        SECOND TRUE
    \else
        SECOND FALSE
    \fi
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert_tokens_startwith(out, expander.expand("FALSE"))
    assert_tokens_endwith(out, expander.expand("SECOND TRUE"))


def test_if_true_false_handler():
    expander = Expander()
    text = r"""
    \iftrue
        TRUE
    \else
        FALSE
    \fi""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert Expander.check_tokens_equal(out, expander.expand("TRUE"))


def test_nested_if_true_false_handler():
    expander = Expander()
    text = r"""
    \iftrue
        TRUE
        \iffalse
            INNER TRUE
        \else
            INNER FALSE
        \fi
    \else
        FALSE
    \fi
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert_tokens_startwith(out, expander.expand("TRUE"))
    assert_tokens_endwith(out, expander.expand("INNER FALSE"))


def test_nopremature_expansion_inside_blocks():
    expander = Expander()
    text = r"""
    \count0=10
    \def\defabc{ABC}

    \iftrue
        \def\atrue{a}
        \defabc
    \else
        % ensure this doesnt run
        \def\bfalse{b}
        \count0=20
    \fi
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert_tokens_startwith(out, expander.expand("ABC"))

    assert expander.get_macro("atrue")
    assert not expander.get_macro("bfalse")
    assert expander.check_tokens_equal(
        expander.expand(r"\the\count0"), expander.expand("10")
    )
