import pytest

from latex2json.expander.expander import Expander
from tests.test_utils import assert_token_sequence


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
