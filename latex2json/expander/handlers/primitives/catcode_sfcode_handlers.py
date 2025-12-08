from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import BACK_TICK_TOKEN, Token, TokenType


def parse_char_value(expander: ExpanderCore) -> Optional[str]:
    """Parse a character value, supporting both `\\X syntax and direct integer"""
    expander.skip_whitespace()

    # Check for backtick syntax: `\\X or `X
    if expander.peek() == BACK_TICK_TOKEN:
        expander.consume()
        expander.skip_whitespace()
        tok = expander.consume()
        if tok is None:
            expander.logger.warning("Expected character after backtick, but found None")
            return None
        char = tok.value

        if len(char) > 1:
            char = char[0]
            expander.logger.info(f"\\catcode only takes one character, using {char}")

        return char

    # Otherwise, try to parse as integer (character code)
    char_code = expander.parse_integer()
    if char_code is None:
        expander.logger.warning("Expected character code or `\\X syntax")
        return None

    if char_code < 0 or char_code > 255:
        expander.logger.warning(f"Character code {char_code} out of range (0-255)")
        return None

    return chr(char_code)


class CatcodeHandler:
    @staticmethod
    def setter(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        char = parse_char_value(expander)
        if char is None:
            return None

        # if not expander.parse_equals():
        #     return []
        expander.parse_equals()

        expander.skip_whitespace()
        new_catcode_int = expander.parse_integer()
        if new_catcode_int is None:
            return []

        if new_catcode_int < 0 or new_catcode_int > 15:
            expander.logger.warning(
                f"Invalid catcode value {new_catcode_int} for \\catcode {char}. Must be 0-15."
            )
            return []  # Return empty list on error

        expander.set_catcode(ord(char), Catcode(new_catcode_int))

        return []

    @staticmethod
    def getter(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        char = parse_char_value(expander)
        if char is None:
            return None

        catcode = expander.get_catcode(ord(char))
        catcode_str = str(catcode.value)
        return expander.convert_str_to_tokens(catcode_str)


class SFCodeHandler:
    @staticmethod
    def setter(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        char = parse_char_value(expander)
        if char is None:
            return None

        if not expander.parse_equals():
            return []

        expander.skip_whitespace()
        value = expander.parse_integer()
        # ignore?

        return []

    @staticmethod
    def getter(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        char = parse_char_value(expander)
        if char is None:
            return None

        catcode = expander.get_catcode(ord(char))
        catcode_str = str(catcode.value)
        return expander.convert_str_to_tokens(catcode_str)


class MathcodeHandler:
    @staticmethod
    def setter(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        char = parse_char_value(expander)
        if char is None:
            return None

        expander.parse_equals()

        expander.skip_whitespace()
        mathcode_value = expander.parse_integer()
        # Parse and ignore, like \sfcode

        return []

    @staticmethod
    def getter(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        char = parse_char_value(expander)
        if char is None:
            return None

        # Return 0 as default mathcode
        return expander.convert_str_to_tokens("0")


def register_catcode_sfcode_handlers(expander: ExpanderCore):
    expander.register_handler("\\catcode", CatcodeHandler.setter, is_global=True)
    expander.register_handler("\\sfcode", SFCodeHandler.setter, is_global=True)
    expander.register_handler("\\mathcode", MathcodeHandler.setter, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    expander.expand(r"\catcode`\]=3")
    print(expander.state.get_catcode(ord("]")))
    expander.expand(r"\catcode`F=3")
    print(expander.state.get_catcode(ord("F")))
