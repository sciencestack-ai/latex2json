import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.catcodes import Catcode
from tests.test_utils import assert_token_sequence


def test_the_catcode():
    expander = Expander()

    expander.expand(r"\catcode`\@=11")
    assert expander.get_catcode(ord("@")) == Catcode.LETTER

    assert_token_sequence(expander.expand(r"\the\catcode`\@"), expander.expand("11"))

    expander.expand(r"\catcode`\@=12")
    assert expander.get_catcode(ord("@")) == Catcode.OTHER

    assert_token_sequence(expander.expand(r"\the\catcode`\@"), expander.expand("12"))


def test_registers():
    expander = Expander()
    expander.expand(r"\newcount\mycount")
    expander.expand(r"\mycount=10")
    assert_token_sequence(expander.expand(r"\the\mycount"), expander.expand("10"))


def test_typeout():
    expander = Expander()

    # typeout consumes immediate token
    assert expander.expand(r"\typeout{Hello, world!}") == []
    assert expander.expand(r"\typeout\foo") == []
    assert expander.check_tokens_equal(
        # consumes immediate token i.e. 1 only
        expander.expand(r"\typeout123"),
        expander.expand("23"),
    )


def test_show():
    # \show mostly used for macros
    expander = Expander()
    assert expander.expand(r"\show\foo") == []

    # \show\count0 -> \show only consumes immediate control sequence i.e. \count. '0' is not consumed
    assert expander.check_tokens_equal(
        expander.expand(r"\show\count0"), expander.expand("0")
    )
