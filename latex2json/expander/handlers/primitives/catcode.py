from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import BACK_TICK_TOKEN, Token, TokenType


def parse_char_for_catcode(expander: ExpanderCore) -> Optional[str]:
    if expander.peek() == BACK_TICK_TOKEN:
        expander.consume()
    else:
        return None

    # check for controlsequence
    tok = expander.peek()
    cmd_name: str | None = None
    if tok.type == TokenType.CONTROL_SEQUENCE:
        cmd_name = tok.value
        expander.consume()
    else:
        expander.logger.warning(
            f"WARNING: \\catcode expected control sequence, but found {tok.value}"
        )
        return None

    char = cmd_name
    if len(char) > 1:
        char = char[0]
        expander.logger.warning(
            f"WARNING: \\catcode only takes one character, using {char}"
        )

    return char


class CatcodeHandler:
    @staticmethod
    def setter(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        char = parse_char_for_catcode(expander)
        if char is None:
            return None

        if not expander.parse_equals():
            return []

        expander.skip_whitespace()
        new_catcode_int = expander.parse_integer()
        if new_catcode_int is None:
            return []

        if new_catcode_int < 0 or new_catcode_int > 15:
            expander.logger.warning(
                f"Error: Invalid catcode value {new_catcode_int} for \\catcode {char}. Must be 0-15."
            )
            return []  # Return empty list on error

        expander.set_catcode(ord(char), Catcode(new_catcode_int))

        return []

    @staticmethod
    def getter(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        char = parse_char_for_catcode(expander)
        if char is None:
            return None

        catcode = expander.get_catcode(ord(char))
        catcode_str = str(catcode.value)
        return expander.convert_str_to_tokens(catcode_str)


def register_catcode(expander: ExpanderCore):
    expander.register_handler("\\catcode", CatcodeHandler.setter, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    expander.expand(r"\catcode`\]=3")
    print(expander.state.get_catcode(ord("]")))
