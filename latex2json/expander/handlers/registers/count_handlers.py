from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.registers import RegisterType
from latex2json.tokens.types import Token, TokenType


class CountHandler:
    @staticmethod
    def setter(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        count_name = expander.parse_integer()
        if count_name is None:
            expander.logger.warning(
                f"Warning: \\count expects a number, but found {expander.peek()}"
            )
            return None

        if not expander.parse_equals():
            expander.logger.warning(
                f"Warning: \\count expects an equals sign, but found {expander.peek()}"
            )
            return None

        expander.skip_whitespace()
        count_value = expander.parse_integer()
        if count_value is None:
            expander.logger.warning(
                f"Warning: \\count expects a number, but found {expander.peek()}"
            )
            return None

        expander.set_register("count", count_name, count_value)
        return []

    @staticmethod
    def getter(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        count_name = expander.parse_integer()
        if count_name is None:
            expander.logger.warning(
                f"Warning: \\count expects a number, but found {expander.peek()}"
            )
            return None

        return expander.get_register_value_as_tokens(RegisterType.COUNT, count_name)


def newcount_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    tok = expander.peek()
    if tok is None or tok.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(f"Warning: \\newcount expects a \name, but found {tok}")
        return None
    count_name = tok.value
    expander.consume()

    expander.create_register(RegisterType.COUNT, count_name, 0, is_global=True)

    return []


def register_count_handlers(expander: ExpanderCore):
    expander.register_handler(r"\count", CountHandler.setter, is_global=True)
    expander.register_handler(r"\newcount", newcount_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    text = r"""
    {
        \newcount\mycounter
        \mycounter = 100
    }
    """
    expander.expand(text)
    expander.expand(r"\the\mycounter")
