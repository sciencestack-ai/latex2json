import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import (
    BEGIN_BRACE_TOKEN,
    END_BRACE_TOKEN,
)
from tests.test_utils import assert_token_sequence


def test_bgroup_egroup():
    expander = Expander()

    # scoped
    out = expander.expand("\\bgroup")  # -> evals to {
    assert_token_sequence(out, [BEGIN_BRACE_TOKEN])

    # test catcode change (local inside scope)
    assert expander.get_catcode(ord("@")) == Catcode.OTHER
    expander.makeatletter()
    assert expander.get_catcode(ord("@")) == Catcode.LETTER

    out = expander.expand("\\egroup")  # -> evals to }
    assert_token_sequence(out, [END_BRACE_TOKEN])

    assert expander.get_catcode(ord("@")) == Catcode.OTHER

    # begin/endgroup

    out = expander.expand(r"\begingroup")  # -> pushes scope but not {
    assert_token_sequence(out, [BEGIN_BRACE_TOKEN])

    # test catcode change (local inside scope)
    expander.makeatletter()
    assert expander.get_catcode(ord("@")) == Catcode.LETTER

    out = expander.expand(r"\endgroup")
    assert_token_sequence(out, [END_BRACE_TOKEN])

    assert expander.get_catcode(ord("@")) == Catcode.OTHER


def test_aftergroup():
    expander = Expander()

    out = expander.expand(r"\begingroup \aftergroup A B\endgroup")
    out_str = expander.convert_tokens_to_str(out).replace(" ", "")
    assert out_str == "{B}A"
