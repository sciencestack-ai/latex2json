from latex2json.nodes.base_nodes import CommandNode
from latex2json.nodes.utils import convert_nodes_to_str
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token


def label_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    label_nodes = parser.parse_brace_as_nodes()
    env_node = parser.current_env
    if env_node:
        label_str = convert_nodes_to_str(label_nodes)
        env_node.labels.append(label_str)
        return []

    # if not found, return generic CommandNode
    return [CommandNode("label", args=[label_nodes])]


def ref_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    ref_nodes = parser.parse_brace_as_nodes()
    # label_str = convert_nodes_to_str(ref_nodes)
    # TODO
    return [CommandNode("ref", args=[ref_nodes])]


def register_ref_label_handlers(parser: ParserCore):
    parser.register_handler("\\label", label_handler)
    parser.register_handler("\\ref", ref_handler)
