import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import (
    BEGIN_BRACE_TOKEN,
    END_BRACE_TOKEN,
    EnvironmentStartToken,
    EnvironmentType,
    Token,
    TokenType,
)
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_prevent_whitelisted_redefinitions():
    expander = Expander(prevent_whitelisted_redefinitions=True)
    assert "normalsize" in expander.white_listed_commands

    # prevent redefinition of white-listed commands e.g. \newcommand
    expander.expand(r"\renewcommand\newcommand{NEWCOMMAND}")
    assert expander.expand(r"\newcommand") == []


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
    # assert_token_sequence(
    #     foo,
    #     [
    #         Token(TokenType.CONTROL_SEQUENCE, "count"),
    #         Token(TokenType.CHARACTER, "0", catcode=Catcode.OTHER),
    #     ],
    # )
    assert_token_sequence(bar, expander.expand("123"))


def test_counter_displays_with_thecountername_redefinitions():
    expander = Expander()
    text = r"""
    \renewcommand{\theequation}{\arabic{section}.\arabic{equation} nice}
    \section{Section 1} % section is now 1
    """
    expander.expand(text)

    # this is now 1.1 due to the redefinition of \theequation
    out = expander.expand(r"\begin{equation}")
    assert_token_sequence(
        out,
        [
            EnvironmentStartToken(
                name="equation", env_type=EnvironmentType.EQUATION, numbering="1.1 nice"
            )
        ],
    )


def test_equation_numbering_with_tags_notags():
    expander = Expander()
    text = r"""
    \begin{equation}
    \tag{1} % manually set tag=1
    \end{equation}

    \begin{equation} % first auto increment tag=1 
    \end{equation}

    \begin{equation} % no tag!
    \notag
    \end{equation}

    \begin{equation} % tag=EU
    \eqno(EU)
    \end{equation}

    \begin{equation} % second auto increment tag=2
    \end{equation}

    \begin{equation*}
    \end{equation*}
    """
    out = expander.expand(text)
    begin_eq_tokens = [
        t for t in out if isinstance(t, EnvironmentStartToken) and "equation" in t.name
    ]
    assert len(begin_eq_tokens) == 6

    assert begin_eq_tokens[0].numbering == "1"
    # note that latex does not check for conflicts
    assert begin_eq_tokens[1].numbering == "1"
    assert begin_eq_tokens[2].numbering is None
    assert begin_eq_tokens[3].numbering == "EU"
    assert begin_eq_tokens[4].numbering == "2"
    assert begin_eq_tokens[5].numbering is None

    # now test with \begin{align}
    text = r"""
    \begin{align}
        row1 \\ %tag=3 (auto increment)
        row2 \nonumber \\ % no tag!
        row3 \tag{XXX} \\ % manually set tag
        row4 % tag = 4 (auto increment)
    \end{align}
    """
    out = expander.expand(text)
    inside_align_eq_tokens = [
        t for t in out if isinstance(t, EnvironmentStartToken) and "equation" in t.name
    ]
    assert len(inside_align_eq_tokens) == 4
    assert inside_align_eq_tokens[0].numbering == "3"
    assert inside_align_eq_tokens[1].numbering is None
    assert inside_align_eq_tokens[2].numbering == "XXX"
    assert inside_align_eq_tokens[3].numbering == "4"


def test_catcode_active_as_control_sequence():
    expander = Expander()

    # test with \def
    text = r"""
\catcode`\� = \active
\def �{EEE}
�

\catcode`\� = 12 % set back to other
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "EEE"

    # test with \newcommand
    text = r"""
\catcode`\| = \active
\newcommand{|}{FFF}
|

\catcode`\| = 12 % set back to other
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "FFF"

    # test with \let
    text = r"""
% mock \active (13) as commands
\def\one{1}\def\three{3}
\catcode`\x = \one\three % 13
\let x=4
x

\catcode`\x = 11 % set back to letter
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "4"

    # CHECK control sequence and active of same value DO NOT CONFLICT
    text = r"""
\catcode`\z = \active\def\z{CONTROL-Z}\def z{ACTIVE-Z}

\z, % CONTROL Z
z % ACTIVE Z

\catcode`\z = 11 % set back to letter

"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_str = out_str.replace("\n", "").replace(" ", "")
    assert out_str == "CONTROL-Z,ACTIVE-Z"


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


def test_def_begin_expansion():
    expander = Expander()

    text = r"""
\def\bea{\begin{equation}}
\def\eea{\end{equation}}

\bea 
1+1
\eea
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out)
    assert (
        out_str.replace("\n", "").replace(" ", "")
        == r"\begin{equation}1+1\end{equation}"
    )


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


def test_recursive_expandafter_loop():
    text = r"""
\def\ddefloop#1{\ifx\ddefloop#1\else\ddef{#1}\expandafter\ddefloop\fi}
% mathbb e.g. \R
\def\ddef#1{\expandafter\def\csname #1\endcsname{\mathbb{#1}}}
\ddefloop ABCDFGHIJKLMNOQRTUVWXYZ\ddefloop
\A \B \Z
"""
    expander = Expander()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == r"\mathbb{A} \mathbb{B} \mathbb{Z}"


def test_character_iteration():
    # examples taken from fancyhdr package

    # iterate over characters in a string
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

    # command to check if character is inside
    text = r"""
\newcommand{\if@in}[4]{%
    \edef\temp@a{#2}\def\temp@b##1#1##2\temp@b{\def\temp@b{##1}}%
    \expandafter\temp@b#2#1\temp@b\ifx\temp@a\temp@b #4\else #3\fi}

    \if@in{c}{abcdef}{TRUE}{FALSE} % c is in abcdef
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "TRUE"

    out = expander.expand(r"\if@in{h}{abcdef}{TRUE}{FALSE}")  # h is not in abcdef
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "FALSE"

    # custom for loop
    text = r"""
\newcommand{\f@nfor}[3]{\edef\@fortmp{#2}%
    \expandafter\@forloop#2,\@nil,\@nil\@@#1{#3}}

    \f@nfor\tempa{a,b,c,d}{\tempa->}
    """
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "a->b->c->d->"


def test_fancyhdr():
    expander = Expander()

    # putting it all together into def@ult
    text = r"""
    \makeatletter

\def\@forc#1#2#3{\expandafter\f@rc\expandafter#1\expandafter{#2}{#3}}
\def\f@rc#1#2#3{\def\temp@ty{#2}\ifx\@empty\temp@ty\else
                                    \f@@rc#1#2\f@@rc{#3}\fi}
\def\f@@rc#1#2#3\f@@rc#4{\def#1{#2}#4\f@rc#1{#3}{#4}}
\newcommand{\if@in}[4]{%
    \edef\temp@a{#2}\def\temp@b##1#1##2\temp@b{\def\temp@b{##1}}%
    \expandafter\temp@b#2#1\temp@b\ifx\temp@a\temp@b #4\else #3\fi}


\newcommand\def@ult[3]{%
  \edef\temp@a{\lowercase{\edef\noexpand\temp@a{#3}}}\temp@a
  \def#1{}%
  \@forc\tmpf@ra{#2}%
    {\expandafter\if@in\tmpf@ra\temp@a{\edef#1{#1\tmpf@ra}}{}}%
  \ifx\@empty#1\def#1{#2}\fi
}

% Test 1: all overlap
\def@ult\cs{xyz}{YXZ}
Test 1: \cs % → "xyz"

% Test 2: partial overlap
\def@ult\cs{abcde}{ACE}
Test 2: \cs % → "ace"

% Test 3: no overlap, fallback to defaults
\def@ult\cs{abc}{XYZ}
Test 3: \cs % → "abc"

% Test 4: mixed case input
\def@ult\cs{aeiou}{U}
Test 4: \cs % → "u"

% Test 5: empty argument
\def@ult\cs{abcd}{}
Test 5: \cs % → "abcd"
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    split = out_str.split("\n")
    split = [s.strip() for s in split if s.strip()]
    assert split == [
        "Test 1: xyz",
        "Test 2: ace",
        "Test 3: abc",
        "Test 4: u",
        "Test 5: abcd",
    ]

    # FINAL BOSS: \f@ncyhf \fancyhf
    text = r"""

    \newcommand{\f@nfor}[3]{\edef\@fortmp{#2}%
    \expandafter\@forloop#2,\@nil,\@nil\@@#1{#3}}
    
    \def\ifancy@mpty#1{\def\temp@a{#1}\ifx\temp@a\@empty}

    \def\fancy@def#1#2{\ifancy@mpty{#2}\fancy@gbl\def#1{\leavevmode}\else
                                    \fancy@gbl\def#1{#2\strut}\fi}

    \let\fancy@gbl\global

    \newcommand{\fancyhf}{\@ifnextchar[{\f@ncyhf\fancyhf{}}%
                                    {\f@ncyhf\fancyhf{}[]}}
        

    \def\f@ncyhf#1#2[#3]#4{%
        \def\temp@c{}%
        \@forc\tmpf@ra{#3}%
            {\expandafter\if@in\tmpf@ra{eolcrhf,EOLCRHF}%
                {}{\edef\temp@c{\temp@c\tmpf@ra}}}%
        \ifx\@empty\temp@c\else
            \@fancyerrmsg{Illegal char `\temp@c' in \string#1 argument:
            [#3]}%
        \fi
        \f@nfor\temp@c{#3}%
            {\def@ult\f@@@eo{eo}\temp@c
            \if@twoside\else
            \if\f@@@eo e\@fancywarning
                {\string#1's `E' option without twoside option is useless}\fi\fi
            \def@ult\f@@@lcr{lcr}\temp@c
            \def@ult\f@@@hf{hf}{#2\temp@c}%
            \@forc\f@@eo\f@@@eo
                {\@forc\f@@lcr\f@@@lcr
                    {\@forc\f@@hf\f@@@hf
                        {\expandafter\fancy@def\csname
                        f@ncy\f@@eo\f@@lcr\f@@hf\endcsname
                        {#4}}}}}}
    \fancyhf{}
    """
    # all this should expand to... nothing!
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == ""


def test_newcommand_RedeclareMathOperator():
    expander = Expander()

    text = r"""
\makeatletter
\newcommand\RedeclareMathOperator{%
  \@ifstar{\def\rmo@s{m}\rmo@redeclare}{\def\rmo@s{o}\rmo@redeclare}%
}
% this is taken from \renew@command
\newcommand\rmo@redeclare[2]{%
  \begingroup \escapechar\m@ne\xdef\@gtempa{{\string#1}}\endgroup
  \expandafter\@ifundefined\@gtempa
     {\@latex@error{\noexpand#1undefined}\@ehc}%
     \relax
  \expandafter\rmo@declmathop\rmo@s{#1}{#2}}
% This is just \@declmathop without \@ifdefinable
\newcommand\rmo@declmathop[3]{%
  \DeclareRobustCommand{#2}{\qopname\newmcodes@#1{#3}}%
}

\RedeclareMathOperator{\div}{div}
$\div$ % becomes \mathop{\mathrm{div}}\nolimits
    """
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert r"\mathop{\mathrm{div}}\nolimits" in out_str

    text = r"""
\RedeclareMathOperator*{\div}{div}
$\div$ % becomes \mathop{\mathrm{div}}\limits
    """
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert r"\mathop{\mathrm{div}}\limits" in out_str


def test_realworld_penalty_dimension_commands():
    text = r"""
    \makeatletter

    \def\@pnumwidth{1.55em}

    \def\l@section#1#2{
        \addpenalty{\@secpenalty} % good place for page break
        \@tempdima 1.5em             % width of box holding section number
        \begingroup
            \parindent  \z@ \rightskip \@pnumwidth
            \parfillskip -\@pnumwidth
            \leavevmode                % TeX command to enter horizontal mode.
            \advance\leftskip\@tempdima %% added 5 Feb 88 to conform to
            \hskip -\leftskip           %% 25 Jan 88 change to \numberline
            %#1\nobreak\hfil \nobreak\hbox to\@pnumwidth{\hss #2}\par
    \endgroup}

    \l@section{Section 1}{1.55em}
"""
    expander = Expander()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == ""
