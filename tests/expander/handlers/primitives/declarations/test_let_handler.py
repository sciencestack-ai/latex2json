import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import (
    assert_token_sequence,
    assert_tokens_endwith,
    assert_tokens_startwith,
)


def test_let():
    expander = Expander()

    text = r"""
    \def\bar{BAR}
    \let\foo\bar % maintains a BAR
    \def\bar{FOO}
    \let\foox\foo % maintains a BAR
"""
    expander.expand(text)
    assert expander.get_macro("foo")
    assert expander.get_macro("bar")
    assert expander.get_macro("foox")
    assert_token_sequence(expander.expand(r"\foo"), expander.expand("BAR"))
    assert_token_sequence(expander.expand(r"\foox"), expander.expand("BAR"))

    text = r"""
    \def\world{World!}
    \def\message{Hello \world}
    \let\greet=\message % copies the definition of message into greet. Which is the literal Hello \world (not expanded!)
    \def\message{NEW MESSAGE}
    \def\world{Universe!}
    \greet % -> Hello Universe!
    """.strip()

    expander.expand(text)
    assert expander.get_macro("greet")
    assert expander.get_macro("message")
    assert expander.get_macro("world")

    assert_token_sequence(expander.expand(r"\message"), expander.expand("NEW MESSAGE"))
    assert_token_sequence(
        expander.expand(r"\greet"), expander.expand("Hello Universe!")
    )

    assert expander.check_macro_is_user_defined("greet")


def test_let_single_token():
    expander = Expander()
    # \let for single token/char
    text = r"""
    \let\greet344 % note that '3' is \greet, 44 is not part of it 
    """.strip()
    out = expander.expand(text)
    assert_token_sequence(out, expander.expand("44 "))

    assert_token_sequence(expander.expand(r"\greet"), expander.expand("3"))

    # \let also grabs whitespace
    text = r"""
    \let\greet= 344 % note that it grabs the whitespace
    """.strip()
    out = expander.expand(text)
    assert_token_sequence(out, expander.expand("344 "))
    assert_token_sequence(expander.expand(r"\greet"), expander.expand(" "))

    # test also works with arbitrary tokens e.g. {}
    expander.expand(r"\let\open={  \let\close=}")
    assert_token_sequence(expander.expand(r"\open"), expander.expand("{"))
    assert_token_sequence(expander.expand(r"\close"), expander.expand("}"))

    # this becomes a brace that is scoped
    text = r"""
    \open
    \let\foo=3
    \close
""".strip()
    out = expander.expand(text)
    # scoped
    assert not expander.get_macro("foo")


def test_let_scope():
    expander = Expander()
    text = r"""
    {
        \let\foo=3
    }
    """.strip()
    expander.expand(text)
    assert not expander.get_macro("foo")

    # now with \global
    text = r"""
    {
    \global\let \foo =344
    }
    """.strip()
    expander.expand(text)
    assert expander.get_macro("foo")
    assert_token_sequence(expander.expand(r"\foo"), expander.expand("3"))


def test_futurelet():
    expander = Expander()
    text = r"""
    \def\lookahead{
        \futurelet\next\checkcolon
    }

    \def\checkcolon{%
        \ifx\next:
            COLON
        \else
            NOT COLON
        \fi
    }
    \lookahead :  % trailing : is in there
""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert_tokens_startwith(out, expander.expand("COLON"))
    assert_tokens_endwith(out, expander.expand(" :"))

    assert expander.check_macro_is_user_defined("lookahead")
    assert expander.check_macro_is_user_defined("checkcolon")


def test_let_preserve_unknown_control_sequence():
    expander = Expander()
    text = r"""
    \let\pminus\pm
    \renewcommand{\pm}{\phi_{\le m}}
    \let\postpm\pm
    """.strip()
    expander.expand(text)
    # \pminus -> \pm is not found, so we preserve it as a control sequence
    assert_token_sequence(
        expander.expand(r"\pminus"),
        [
            Token(TokenType.CONTROL_SEQUENCE, "pm"),
        ],
    )
    # \postpm -> \pm is defined, so we copy its definition
    assert_token_sequence(
        expander.expand(r"\postpm"),
        expander.expand(r"\pm"),
    )


def test_let_can_be_anything():
    expander = Expander()

    # test that let that be any macro, including \def itself
    text = r"""
    \let\mydef\def
    \mydef\xxx#1{XXX: #1}
    \xxx{123}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "XXX: 123"

    # test_let_on_text_cmd
    text = r"""
    \let\rom\textbf
    \rom{a}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == r"\textbf{a}"

    # test let on ifs
    text = r"""
    \makeatletter
\let\if@mathematic\iftrue
\if@mathematic
    MATHEMATIC
\else
    NOT MATHEMATIC
\fi
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "MATHEMATIC"

    # test let on noexpand expandafter
    text = r"""
\let\@xp=\expandafter
\let\@nx=\noexpand
\@xp\@nx\csname title\endcsname % should be \title token itself
% expandafter expands \csname...\endname, which becomes \title literal
% noexpand \title becomes \title token itself
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == r"\title"


def test_LetLtxMacro():
    expander = Expander()
    text = r"""
    \LetLtxMacro{\oldsqrt}{\sqrt}
    $\oldsqrt{2}$
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == r"$\sqrt{2}$"
