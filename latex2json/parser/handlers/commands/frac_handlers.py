from latex2json.nodes import FootnoteNode
from latex2json.nodes.base_nodes import TextNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token
from latex2json.parser.handlers.commands.command_handler_utils import (
    register_ignore_handlers_util,
)


def frac_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    block1 = parser.parse_immediate_node()
    parser.skip_whitespace()
    block2 = parser.parse_immediate_node()
    return block1 + [TextNode("/")] + block2


def register_frac_handlers(parser: ParserCore):
    for frac_command in ["nicefrac", "sfrac"]:
        parser.register_handler(frac_command, frac_handler)


if __name__ == "__main__":
    from latex2json.parser.parser import Parser

    parser = Parser()
    register_frac_handlers(parser)

    text = r"""
    \nicefrac 12
    \sfrac{AAA} {BBB}
    """

    out = parser.parse(text)
    print(out)
