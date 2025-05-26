import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_bgroup_egroup():
    expander = Expander()

    # scoped
    expander.expand("\\bgroup")

    # test catcode change (local inside scope)
    assert expander.get_catcode(ord("@")) == Catcode.OTHER
    expander.set_catcode(ord("@"), Catcode.LETTER)
    assert expander.get_catcode(ord("@")) == Catcode.LETTER

    expander.expand("\\egroup")
    assert expander.get_catcode(ord("@")) == Catcode.OTHER


def test_catcode():
    expander = Expander()
    assert expander.get_catcode(ord("]")) == Catcode.OTHER
    expander.expand(r"\catcode`\]=3")
    assert expander.get_catcode(ord("]")) == 3

    # test on scopes and global
    text = r"""
    {
    \catcode`\]=4 % local to scope
    }
    """
    expander.expand(text)
    assert expander.get_catcode(ord("]")) == 3

    # now let's test with \global
    text = r"""
    {
    \global\catcode`\]=5
    }
    """
    expander.expand(text)
    assert expander.get_catcode(ord("]")) == 5


def test_makeatletter_makeatother():
    expander = Expander()

    assert expander.get_catcode(ord("@")) == Catcode.OTHER

    expander.expand("\\makeatletter")
    assert expander.get_catcode(ord("@")) == Catcode.LETTER

    expander.expand("\\makeatother")
    assert expander.get_catcode(ord("@")) == Catcode.OTHER


def test_redefine_primitives():
    expander = Expander()

    assert expander.get_macro("\\newcommand")
    assert expander.get_macro("\\def")

    # let's try to redefine \newcommand
    text = r"""
    \def\newcommand{NEWCOMMAND}
    """
    expander.expand(text)
    assert_token_sequence(
        expander.expand(r"\newcommand"), expander.expand("NEWCOMMAND")
    )


def test_edef_with_counters():
    expander = Expander()

    text = r"""
    \count0=123
    \edef\foo{\count0}  % → literally expands to "\count0", NOT "123"
    \edef\bar{\the\count0}  % → expands to "123"
""".strip()
    expander.expand(text)
    foo = expander.expand(r"\foo")
    bar = expander.expand(r"\bar")
    assert_token_sequence(
        foo,
        [
            Token(TokenType.CONTROL_SEQUENCE, "count"),
            Token(TokenType.CHARACTER, "0", catcode=Catcode.OTHER),
        ],
    )
    assert_token_sequence(bar, expander.expand("123"))


def test_makeatletter_futurelet_ifx_lookahead():
    expander = Expander()

    text = r"""

\makeatletter

% 1. Generic lookahead function
\def\lookahead{\futurelet\next\@check}

% 2. Dispatch logic
\def\@check{%
  \ifx\next\bgroup
    [lookahead] Next token is a group!%
  \else
    \ifx\next\somecmd
      [lookahead] Next token is \string\somecmd!%
    \else
      [lookahead] Next token is something else.
    \fi
  \fi
}

% 3. Dummy macro for testing
\def\somecmd{This is a macro.}
""".strip()
    expander.expand(text)

    input_expstart_expend = [
        (r"\lookahead{123}", r"[lookahead] Next token is a group!", r"{123}"),
        (
            r"\lookahead\somecmd",
            r"[lookahead] Next token is \somecmd!",
            r"This is a macro.",
        ),
        (r"\lookahead!", r"[lookahead] Next token is something else.", r"!"),
    ]

    for input, exp_start, exp_end in input_expstart_expend:
        out = expander.expand(input)
        out = strip_whitespace_tokens(out)
        out_as_str = expander.convert_tokens_to_str(out)
        assert out_as_str.startswith(exp_start)
        assert out_as_str.endswith(exp_end)
