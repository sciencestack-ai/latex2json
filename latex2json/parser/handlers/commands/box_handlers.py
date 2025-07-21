from typing import List, Optional

from latex2json.expander.state import ProcessingMode
from latex2json.nodes import ASTNode
from latex2json.nodes.base_nodes import CommandNode, TextNode
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.handlers.commands.command_handler_utils import (
    make_generic_command_handler,
)
from latex2json.parser.parser_core import Handler, ParserCore
from latex2json.latex_maps.boxes import (
    BASE_BOXES,
    ADVANCED_BOX_SPECS,
    KATEX_SUPPORTED_BOXES,
)
from latex2json.tokens.types import Token, TokenType


def make_box_handler(cmd: str, argspec: str) -> Handler:
    base_handler = make_generic_command_handler(cmd, argspec, postprocess_args=True)
    is_katex_supported = cmd in KATEX_SUPPORTED_BOXES

    def handler(parser: ParserCore, token: Token) -> List[ASTNode]:
        is_math_mode = parser.is_math_mode
        if is_math_mode:
            parser.push_mode(ProcessingMode.TEXT)
        nodes = base_handler(parser, token)
        if is_math_mode:
            parser.pop_mode()
        return nodes

    def box_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
        nodes = handler(parser, token)
        if not nodes:
            return []
        cmd_node = nodes[0]
        if not isinstance(cmd_node, CommandNode):
            # sth went wrong with command handler
            return []

        if not cmd_node.args:
            return []

        # all the content of \box... is in the last arg
        last_arg = cmd_node.args[-1]
        if not last_arg:
            return []

        last_arg = strip_whitespace_nodes(last_arg)

        if parser.is_math_mode:

            if is_katex_supported:
                # if mathmode, we wrap it as one single TextNode containing the raw string
                return [TextNode(cmd_node.detokenize())]

            # if not katex supported, just use hbox (which is katex supported) and convert to string i.e. \hbox{...}
            last_arg_str = "".join(child.detokenize() for child in last_arg)
            if cmd == "mbox":
                # strip out all "\n"
                last_arg_str = last_arg_str.replace("\n", "")
            return [TextNode("\\hbox{%s}" % (last_arg_str))]

        # return the last arg as is
        return last_arg

    return box_handler


def register_box_handlers(parser: ParserCore):
    for cmd in BASE_BOXES:
        parser.register_handler(cmd, make_box_handler(cmd, "{"))

    for cmd, spec in ADVANCED_BOX_SPECS.items():
        parser.register_handler(cmd, make_box_handler(cmd, spec))


if __name__ == "__main__":
    from latex2json.parser.parser import Parser

    parser = Parser()
    register_box_handlers(parser)

    # tokens = [Token(type=TokenType.CONTROL_SEQUENCE, value="raisebox")]
    # tokens += parser.expander.convert_str_to_tokens("{1in}{sometext$1+1$}")

    # parser.push_mode(ProcessingMode.MATH_DISPLAY)
    # out = parser.process_tokens(tokens)
    # print(out)

    text = r"""
    $\raisebox{1in}[]{sometext$1+1$}$
"""

    out = parser.parse(text)
    print(out)
