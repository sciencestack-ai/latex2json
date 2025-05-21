from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.registers import RegisterType, set_register_handler
from latex2json.tokens.types import Token, TokenType


DIMEN_TYPE = RegisterType.DIMEN


class DimenHandler:
    @staticmethod
    def setter(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        dimen_name = expander.parse_integer()
        if dimen_name is None:
            expander.logger.warning(
                f"Warning: \\dimen expects a number, but found {expander.peek()}"
            )
            return None

        if not set_register_handler(expander, DIMEN_TYPE, dimen_name):
            expander.logger.warning(
                f"Warning: \\dimen expects an equals sign, but found {expander.peek()}"
            )
            return None

        return []

    @staticmethod
    def getter(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        dimen_name = expander.parse_integer()
        if dimen_name is None:
            expander.logger.warning(
                f"Warning: \\dimen expects a number, but found {expander.peek()}"
            )
            return None

        return expander.get_register_value_as_tokens(DIMEN_TYPE, dimen_name)


def newdimen_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    tok = expander.peek()
    if tok is None or tok.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(f"Warning: \\newdimen expects a \name, but found {tok}")
        return None
    dimen_name = tok.value
    expander.consume()

    expander.create_register(DIMEN_TYPE, dimen_name, 0, is_global=True)

    return []


def register_dimen_handlers(expander: ExpanderCore):
    expander.register_handler(r"\dimen", DimenHandler.setter, is_global=True)
    expander.register_handler(r"\newdimen", newdimen_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    text = r"""
    {
        \newdimen\mylength
    }
    \mylength = 10pt
    """
    expander.expand(text)
    out = expander.expand(r"\the\mylength")
