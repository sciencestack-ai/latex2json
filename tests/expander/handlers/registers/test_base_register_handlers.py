from latex2json.expander.expander import Expander
from latex2json.expander.handlers.registers.base_register_handlers import (
    register_base_register_macros,
)
from latex2json.latex_maps.dimensions import dimension_to_scaled_points
from latex2json.registers import RegisterType
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens


def test_register_macros():
    expander = Expander()

    for register_type in RegisterType:
        assert expander.get_macro(register_type.value)

    # test on dim direct expand
    expander.expand(r"\dimen20=10pt")
    assert expander.get_register_value(RegisterType.DIMEN, 20) > 0

    # does not expand by itself
    out = expander.expand(r"\dimen20")
    assert expander.check_tokens_equal(
        out,
        [
            Token(TokenType.CONTROL_SEQUENCE, "dimen"),
            Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "0", catcode=Catcode.OTHER),
        ],
    )


def test_new_register_macros():
    expander = Expander()

    # count
    expander.expand(r"\newcount\mycount")
    assert expander.get_register_value(RegisterType.COUNT, "mycount") == 0

    expander.expand(r"\mycount=10")
    assert expander.get_register_value(RegisterType.COUNT, "mycount") == 10

    # dimen
    expander.expand(r"\newdimen\mydimen")
    assert expander.get_register_value(RegisterType.DIMEN, "mydimen") == 0

    expander.expand(r"\mydimen=10pt")
    assert expander.get_register_value(RegisterType.DIMEN, "mydimen") > 0

    # skip
    expander.expand(r"\newskip\myskip")
    assert expander.get_register_value(RegisterType.SKIP, "myskip") == 0

    # toks
    expander.expand(r"\newtoks\mytoks")
    assert expander.get_register_value(RegisterType.TOKS, "mytoks") == []

    expander.expand(r"\mytoks={abc}")
    assert expander.get_register_value(RegisterType.TOKS, "mytoks") == expander.expand(
        "abc"
    )


def test_toks():
    expander = Expander()

    expander.expand(r"\newtoks\mytoks")
    out = expander.expand(r"\mytoks={abc}")
    assert len(out) == 0

    out = expander.expand(r"\the\mytoks")
    assert expander.check_tokens_equal(out, expander.expand("abc"))

    # test in scope (the new registers are global, but assignments are local)
    text = r"""
        \newtoks\tokker
        \tokker={123}
        \the\tokker
    """.strip()
    expander.push_scope()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)

    tokens_123 = expander.expand("123")
    assert expander.check_tokens_equal(out, tokens_123)
    assert expander.state.get_register(RegisterType.TOKS, "tokker")
    assert expander.get_register_value(RegisterType.TOKS, "tokker") == tokens_123
    expander.pop_scope()

    # after scope, register is back to default
    assert expander.state.get_register(RegisterType.TOKS, "tokker") == []
    assert expander.expand(r"\the\tokker") == []


def test_skips():
    expander = Expander()

    expander.expand(r"\newskip\myskip")
    expander.expand(r"\myskip=10pt plus 2pt minus 5pt")

    expected_pt = dimension_to_scaled_points(10 + 2 - 5, "pt")

    assert expander.get_register_value(RegisterType.SKIP, "myskip") == expected_pt

    # test with dimensions too
    expander.expand(r"\newdimen\mydimen \mydimen=10pt")
    # expander.expand(r"\myskip=10pt plus 2pt")
    # assert expander.get_register_value(RegisterType.SKIP, "myskip") == pt10 + pt2

    # expander.expand(r"\myskip=10pt plus 2pt minus 5pt")
    # assert expander.get_register_value(RegisterType.SKIP, "myskip") == pt10 + pt2 - pt5
