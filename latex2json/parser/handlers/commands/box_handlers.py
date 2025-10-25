from typing import List, Optional

from latex2json.expander.state import ProcessingMode
from latex2json.nodes import ASTNode
from latex2json.nodes.base_nodes import CommandNode, TextNode
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.handlers.commands.command_handler_utils import (
    make_generic_command_handler,
)
from latex2json.parser.handlers.commands.text_handlers import (
    merge_nodes_in_mathmode_text,
)
from latex2json.parser.parser_core import Handler, ParserCore
from latex2json.registers.defaults.boxes import (
    BASE_BOXES,
    ADVANCED_BOX_SPECS,
    KATEX_SUPPORTED_BOXES,
)
from latex2json.tokens.types import Token, TokenType


def make_box_handler(cmd: str, argspec: str) -> Handler:
    base_handler = make_generic_command_handler(cmd, argspec, postprocess_args=True)
    is_katex_supported = cmd in KATEX_SUPPORTED_BOXES

    def text_mode_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
        is_math_mode = parser.is_math_mode
        preserve_braces_as_text = parser.preserve_braces_as_text
        if is_math_mode:
            parser.preserve_braces_as_text = True
            parser.push_mode(ProcessingMode.TEXT)
        nodes = base_handler(parser, token)
        if is_math_mode:
            parser.pop_mode()
            parser.preserve_braces_as_text = preserve_braces_as_text
        return nodes

    def box_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
        nodes = text_mode_handler(parser, token)
        if not nodes:
            return []
        cmd_node = nodes[0]
        if not isinstance(cmd_node, CommandNode):
            # sth went wrong with generic command handler
            return []

        if not cmd_node.args:
            return []

        # all the content of \box... is in the last arg
        last_arg = cmd_node.args[-1]
        if not last_arg:
            return []

        last_arg = strip_whitespace_nodes(last_arg)

        if parser.is_math_mode:
            # if not katex supported, just use hbox (which is katex supported)
            box_cmd = "\\hbox"
            if is_katex_supported:
                # get entire cmd up to last arg (which is the content itself) as string
                # e.g. \colorbox{red}{...} -> \colorbox{red}
                cmd_node.args = cmd_node.args[:-1]
                box_cmd = cmd_node.detokenize()

            if cmd == "mbox":
                # strip out all "\n"
                for arg in last_arg:
                    if isinstance(arg, TextNode):
                        arg.text = arg.text.replace("\n", "")

            return merge_nodes_in_mathmode_text(box_cmd, last_arg)

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

    text = r"""
    $\raisebox{1in}[]{sometext$1+1$ \ref{eq:22} abc}$
"""

    out = parser.parse(text)
    print(out)
