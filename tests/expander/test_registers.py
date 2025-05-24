import pytest

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.registers import (
    Glue,
    RegisterType,
    TexRegisters,
)
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.tokenizer import Tokenizer
from latex2json.tokens.types import Token, TokenType


# def test_get_register_handler():
#     expander = ExpanderCore()

#     expander.register_macro(r"\count", RegisterMacro(RegisterType.COUNT, "count"))
#     expander.set_text(r"\count3")

#     tok = expander.consume()
#     assert tok == Token(TokenType.CONTROL_SEQUENCE, "count")
#     assert get_register_handler(expander, tok) == (RegisterType.COUNT, 3)
#     assert expander.eof()


# def test_register_assignment():
#     expander = ExpanderCore()

#     expander.set_text(r"\count0=10")
#     assert expander.consume() == Token(TokenType.CONTROL_SEQUENCE, "count")
#     assert expander.consume() == Token(TokenType.CHARACTER, "0", catcode=Catcode.OTHER)
#     assert expander.peek().value == "="
#     assert set_register_value_handler(expander, RegisterType.COUNT, 0)
#     assert expander.get_register_value(RegisterType.COUNT, 0) == 10

#     # test dimensions
#     expander.set_text(r"\dimen9=10pt")
#     assert expander.consume() == Token(TokenType.CONTROL_SEQUENCE, "dimen")
#     assert expander.consume() == Token(TokenType.CHARACTER, "9", catcode=Catcode.OTHER)
#     assert expander.peek().value == "="
#     assert set_register_value_handler(expander, RegisterType.DIMEN, 9)
#     assert expander.get_register_value(RegisterType.DIMEN, 9) > 0
