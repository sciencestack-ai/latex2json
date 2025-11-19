from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.registers.base_register_handlers import (
    parse_register_setter,
)
from latex2json.tokens.types import Token, TokenType


def make_advance_handler(operation: str = "add"):
    def advance_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        # Skip any whitespace after \advance
        expander.skip_whitespace()

        parsed = expander.parse_register()
        # if not parsed:
        #     expander.logger.warning(
        #         f"\\advance expects a register, but found {expander.peek()}"
        #     )
        #     return None

        # Skip whitespace before "by"
        expander.skip_whitespace()

        # Parse optional "by" keyword
        b_token = expander.peek()
        y_token = expander.peek(1)
        # dont need to check for peek(2) is whitespace; latex greedily parses 'by' verbatim e.g. \advance\count1 bye 10 -> the by will be consumed
        if b_token and b_token.value == "b" and y_token and y_token.value == "y":
            expander.consume()
            expander.consume()
            # Skip whitespace after "by"
            expander.skip_whitespace()

        tok = expander.peek()
        if tok is None:
            expander.logger.warning(f"\\advance [by] expects a value, but found {tok}")
            return None

        if not parsed:
            return None

        register_type, register_name = parsed

        value = parse_register_setter(expander, register_type)
        if value is None or not isinstance(value, int | float):
            expander.logger.warning(
                f"\\advance [by] expects a number, but found {value}"
            )
            return None

        cur_value = expander.get_register_value(register_type, register_name)
        if cur_value is None:
            return None
        try:
            if operation == "add":
                new_value = cur_value + value
            elif operation == "subtract":
                new_value = cur_value - value
            elif operation == "multiply":
                new_value = cur_value * value
            elif operation == "divide":
                new_value = cur_value / value if value != 0 else 0

            new_value = int(new_value)
            expander.set_register(register_type, register_name, new_value)
        except Exception as e:
            expander.logger.warning(
                f"Could not {operation} {value} to {cur_value} in register {register_name}"
            )
            return None

        return []

    return advance_handler


def register_advance_handler(expander: ExpanderCore):
    expander.register_handler(r"\advance", make_advance_handler("add"), is_global=True)
    expander.register_handler(
        r"\divide", make_advance_handler("divide"), is_global=True
    )
    expander.register_handler(
        r"\multiply", make_advance_handler("multiply"), is_global=True
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_advance_handler(expander)

    expander.expand(r"\newdimen\mydimen")

    # test with multiplier
    expander.expand(r"\advance \mydimen by 10 pt")
    expander.expand(r"\def\defmydimen{\mydimen}")
    expander.expand(r"\advance \mydimen by 0.5\defmydimen")
    out = expander.expand(r"\the\mydimen")
    print(out)
