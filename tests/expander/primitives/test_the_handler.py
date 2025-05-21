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
