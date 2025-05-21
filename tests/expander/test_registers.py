import pytest

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.registers import (
    Glue,
    RegisterType,
    get_register_handler,
    register_all_register_macros,
    set_register_value_handler,
    TexRegisters,
    RegisterMacro,
)
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.tokenizer import Tokenizer
from latex2json.tokens.types import Token, TokenType


def test_get_register_handler():
    expander = ExpanderCore()

    expander.register_macro(r"\count", RegisterMacro(RegisterType.COUNT, "count"))
    expander.set_text(r"\count3")

    tok = expander.consume()
    assert tok == Token(TokenType.CONTROL_SEQUENCE, "count")
    assert get_register_handler(expander, tok) == (RegisterType.COUNT, 3)
    assert expander.eof()


def test_register_assignment():
    expander = ExpanderCore()

    expander.set_text(r"\count0=10")
    assert expander.consume() == Token(TokenType.CONTROL_SEQUENCE, "count")
    assert expander.consume() == Token(TokenType.CHARACTER, "0", catcode=Catcode.OTHER)
    assert expander.peek().value == "="
    assert set_register_value_handler(expander, RegisterType.COUNT, 0)
    assert expander.get_register_value(RegisterType.COUNT, 0) == 10

    # test dimensions
    expander.set_text(r"\dimen9=10pt")
    assert expander.consume() == Token(TokenType.CONTROL_SEQUENCE, "dimen")
    assert expander.consume() == Token(TokenType.CHARACTER, "9", catcode=Catcode.OTHER)
    assert expander.peek().value == "="
    assert set_register_value_handler(expander, RegisterType.DIMEN, 9)
    assert expander.get_register_value(RegisterType.DIMEN, 9) > 0


def test_register_macros():
    expander = ExpanderCore()
    register_all_register_macros(expander)

    for register_type in RegisterType:
        assert expander.get_macro(register_type.value)

    expander.set_text(r"\count20=10")
    assert expander.parse_register() == (RegisterType.COUNT, 20)
    assert expander.peek().value == "="
    assert set_register_value_handler(expander, RegisterType.COUNT, 20)

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
    expander = ExpanderCore()
    register_all_register_macros(expander)

    expander.expand(r"\newcount\mycount")
    assert expander.get_register_value(RegisterType.COUNT, "mycount") == 0

    expander.expand(r"\mycount=10")
    assert expander.get_register_value(RegisterType.COUNT, "mycount") == 10

    expander.expand(r"\newdimen\mydimen")
    assert expander.get_register_value(RegisterType.DIMEN, "mydimen") == 0

    expander.expand(r"\mydimen=10pt")
    assert expander.get_register_value(RegisterType.DIMEN, "mydimen") > 0

    expander.expand(r"\newskip\myskip")
    assert expander.get_register_value(RegisterType.SKIP, "myskip") == Glue(0, 0, 0)
