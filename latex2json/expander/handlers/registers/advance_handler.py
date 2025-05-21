from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token, TokenType
from latex2json.expander.handlers.registers.count_handlers import CountHandler
from latex2json.tokens.utils import is_whitespace_token


class AdvanceHandler:
    @staticmethod
    def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        # Skip any whitespace after \advance
        expander.skip_whitespace()

        # Get the register name/number
        tok = expander.peek()
        if tok is None or tok.type != TokenType.CONTROL_SEQUENCE:
            expander.logger.warning(
                f"Warning: \\advance expects a register name, but found {tok}"
            )
            return None
        register_name = tok.value
        expander.consume()

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
            expander.logger.warning(
                f"Warning: \\advance\\{register_name} [by] expects a value, but found {tok}"
            )
            return None

        # # Get the increment value
        # increment = expander.parse_integer()
        # if increment is None:
        #     expander.logger.warning(
        #         f"Warning: \\advance expects a number after 'by', but found {expander.peek()}"
        #     )
        #     return None

        # # Get the current value and add the increment
        # register_name = CountHandler.COUNT_PREFIX + str(count_name)
        # current_value = expander.get_register_value(register_name)

        # if current_value is None:
        #     current_value = 0  # Initialize to 0 if register doesn't exist

        # new_value = current_value + increment

        # # Set the new value
        # expander.set_register(register_name, new_value)

        return []


def register_advance_handler(expander: ExpanderCore):
    expander.register_handler(r"\advance", AdvanceHandler.handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    expander.expand(r"\advance\count1 by 10")
    print(expander.get_register_value("count", 1))
