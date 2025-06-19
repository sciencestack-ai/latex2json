from typing import Optional
from latex2json.nodes.base_nodes import GroupNode
from latex2json.nodes.caption_node import CaptionNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token


def subfloat_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    caption = parser.parse_bracket_as_nodes()
    parser.skip_whitespace()
    body = parser.parse_brace_as_nodes() or []

    caption_nodes = [CaptionNode(caption)] if caption else []
    return [GroupNode(caption_nodes + body)]


def register_subfloat_handler(parser: ParserCore):
    parser.register_handler("subfloat", subfloat_handler)
