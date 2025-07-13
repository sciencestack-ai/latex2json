import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_bgroup_egroup():
    expander = Expander()

    # scoped
    out = expander.expand("\\bgroup")  # -> evals to {
    assert_token_sequence(out, [BEGIN_BRACE_TOKEN])

    # test catcode change (local inside scope)
    assert expander.get_catcode(ord("@")) == Catcode.OTHER
    expander.set_catcode(ord("@"), Catcode.LETTER)
    assert expander.get_catcode(ord("@")) == Catcode.LETTER

    out = expander.expand("\\egroup")  # -> evals to }
    assert_token_sequence(out, [END_BRACE_TOKEN])

    assert expander.get_catcode(ord("@")) == Catcode.OTHER

    # begin/endgroup

    out = expander.expand(r"\begingroup")  # -> pushes scope but not {
    assert_token_sequence(out, [])

    # test catcode change (local inside scope)
    expander.set_catcode(ord("@"), Catcode.LETTER)
    assert expander.get_catcode(ord("@")) == Catcode.LETTER

    out = expander.expand(r"\endgroup")
    assert_token_sequence(out, [])

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


def test_mathmode_expansions_with_braces():
    text = r"""
    \newcommand{\abs}[1]{\left\vert#1\right\vert}
    \newcommand{\ti}{\tilde}
    \newcommand{\calR}{\mathcal R}
    \newcommand{\gab}{g^{\alpha\beta}}
    \newcommand{\paa}{\partial_\alpha}
    \newcommand{\f}{\frac}
    \newcommand{\la}{\left\vert}

    $\abs{x}$ % \left\vert{x}\right\vert
    $\ti{3}$ % $\tilde{3}$
    $\frac\calR 2$ % $\frac{\mathcal R} 2$
    $\paa\gab$ % \partial_\alpha{g^{\alpha\beta}}
    $\Delta^\paa$ % \Delta^\partial_\alpha
    $x^\f{1}{2}$ % x^\frac{1}{2}
    $\la \nabla_{x,y}$ % \left\vert \nabla_{x,y}
    $\chi(x-x_0) \la$ % \chi(x-x_0) \left\vert
    """.strip()
    expander = Expander()
    expander.expand(text)

    expected_pairs = [
        (r"$\abs{x}$", r"$\left\vert{x}\right\vert$"),
        (r"$\ti{3}$", r"$\tilde{3}$"),
        (r"$\frac\calR 2$", r"$\frac{\mathcal R} 2$"),
        (r"$\paa\gab$", r"$\partial_\alpha{g^{\alpha\beta}}$"),
        (r"$\Delta^\paa$", r"$\Delta^\partial_\alpha$"),
        (r"$x^\f{1}{2}$", r"$x^\frac{1}{2}$"),
        (r"$\la \nabla_{x,y}$", r"$\left\vert \nabla_{x,y}$"),
        (r"$\chi(x-x_0) \la$", r"$\chi(x-x_0) \left\vert$"),
    ]

    for input, expected in expected_pairs:
        assert_token_sequence(expander.expand(input), expander.expand(expected))


def test_tail_recursion_countdown():
    expander = Expander()

    text = r"""
\def\countdown#1{%
  \ifnum#1>0
    Number: #1
    \expandafter\countdown\expandafter{\number\numexpr#1-1\relax}%
  \fi
}
\countdown{5}
"""

    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out)
    sequence = out_str.split("\n")
    sequence = [s.strip() for s in sequence if s.strip()]
    assert sequence == ["Number: 5", "Number: 4", "Number: 3", "Number: 2", "Number: 1"]


def test_loop_csname():
    text = r"""
% Define a primitive forloop
\def\myforloop#1#2#3#4{%
  % #1 = counter name
  % #2 = start value  
  % #3 = end value
  % #4 = body
  \expandafter\newcount\csname #1\endcsname
  \csname #1\endcsname=#2\relax
  \loop
    #4%
    \advance\csname #1\endcsname by 1
  \ifnum\csname #1\endcsname<#3
  \repeat
}

% Usage:
\myforloop{i}{1}{6}{Item \the\i}    
"""
    expander = Expander()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out)
    sequence = out_str.replace("\n", "").replace(" ", "")
    assert sequence == "Item1Item2Item3Item4Item5"


def test_character_iteration():
    # taken from fancyhdr package
    text = r"""
\makeatletter
\def\@forc#1#2#3{\expandafter\f@rc\expandafter#1\expandafter{#2}{#3}}
\def\f@rc#1#2#3{\def\temp@ty{#2}\ifx\@empty\temp@ty\else
                                    \f@@rc#1#2\f@@rc{#3}\fi}
\def\f@@rc#1#2#3\f@@rc#4{\def#1{*#2*}#4\f@rc#1{#3}{#4}}

\@forc\x{hello}{\x}
"""
    expander = Expander()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "*h**e**l**l**o*"
