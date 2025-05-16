from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.nodes.base import ASTNode
from latex2json.nodes.syntactic_nodes import CommandNode
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType

BACK_TICK_TOKEN = Token(TokenType.CHARACTER, value="`", catcode=Catcode.OTHER)


def catcode_handler(
    expander: ExpanderCore, node: CommandNode
) -> Optional[List[ASTNode]]:
    parser = expander.parser

    """need check for `"""
    if expander.peek() == BACK_TICK_TOKEN:
        expander.consume()
    else:
        return None

    # check for controlsequence
    cmd: CommandNode | None = None
    if parser.match(TokenType.CONTROL_SEQUENCE):
        cmd = parser.parse_command()

    if not cmd:
        return None

    char = cmd.name.lstrip("\\")
    if len(char) > 1:
        char = char[0]
        expander.logger.warning(
            f"WARNING: \\catcode only takes one character, using {char}"
        )

    expander.skip_whitespace()
    if not parser.parse_equals():
        return None

    expander.skip_whitespace()
    new_catcode_int = parser.parse_integer()
    if new_catcode_int is None:
        return None

    if new_catcode_int < 0 or new_catcode_int > 15:
        expander.logger.warning(
            f"Error: Invalid catcode value {new_catcode_int} for \\catcode {char}. Must be 0-15."
        )
        return []  # Return empty list on error

    expander.set_catcode(ord(char), Catcode(new_catcode_int))

    return []


def register_catcode(expander: ExpanderCore):
    expander.register_handler("\\catcode", catcode_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    expander.expand(r"\catcode`\]=3")
    print(expander.state.get_catcode(ord("]")))
