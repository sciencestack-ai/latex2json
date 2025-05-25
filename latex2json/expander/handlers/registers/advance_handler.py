from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.registers.base_register_handlers import (
    parse_registertype_value,
)
from latex2json.tokens.types import Token, TokenType


class AdvanceHandler:
    @staticmethod
    def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        # Skip any whitespace after \advance
        expander.skip_whitespace()

        parsed = expander.parse_register()
        if not parsed:
            expander.logger.warning(
                f"Warning: \\advance expects a register, but found {expander.peek()}"
            )
            return None

        register_type, register_name = parsed

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

        value = parse_registertype_value(expander, register_type)
        if value is None:
            expander.logger.warning(
                f"Warning: \\advance\\{register_name} [by] expects a value, but found {tok}"
            )
            return None

        expander.increment_register(register_type, register_name, value)

        return []


def register_advance_handler(expander: ExpanderCore):
    expander.register_handler(r"\advance", AdvanceHandler.handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_advance_handler(expander)

    # expander.expand(r"\def\cnter{\count} \def\one{1}")
    # expander.expand(r"\advance\count1 by 10")
    # expander.expand(r"\advance\cnter\one by 20")
    # print(expander.get_register_value(RegisterType.COUNT, 1))

    expander.expand(r"\newcount\mycount")
    expander.expand(r"\advance\mycount by 10")
    print(expander.expand(r"\the\mycount"))
