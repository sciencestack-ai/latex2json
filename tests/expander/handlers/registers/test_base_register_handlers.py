from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.registers.base_register_handlers import (
    register_base_register_macros,
)
from latex2json.registers import Glue, RegisterType
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType


def test_register_macros():
    expander = ExpanderCore()
    register_base_register_macros(expander)

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
    expander = ExpanderCore()
    register_base_register_macros(expander)

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
