from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


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

        return expander.get_register_value_as_tokens("count", count_name)


def register_count_handlers(expander: ExpanderCore):
    expander.register_handler(r"\count", CountHandler.setter, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    expander.expand(r"\count10=100")
    print(expander.state.get_register("count", 10))
