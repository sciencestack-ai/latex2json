from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token


def label_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    label_value = parser.parse_brace_as_nodes()
    label_str = parser.convert_nodes_to_str(label_value)
    env_node = parser.current_env
    if env_node:
        env_node.labels.append(label_str)
    return []


def ref_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    label_value = parser.parse_brace_as_nodes()
    label_str = parser.convert_nodes_to_str(label_value)
    # TODO
    return []


def register_ref_label_handlers(parser: ParserCore):
    parser.register_handler("\\label", label_handler)
    parser.register_handler("\\ref", ref_handler)
