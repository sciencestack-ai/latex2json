from latex2json.nodes import CommandNode, RefNode
from latex2json.nodes.utils import convert_nodes_to_str
from latex2json.parser.handlers.handler_utils import make_generic_command_handler
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


def make_ref_handler(split_comma: bool = False):
    def ref_handler(parser: ParserCore, token: Token):
        parser.parse_asterisk()
        parser.skip_whitespace()
        ref_nodes = parser.parse_brace_as_nodes()
        if ref_nodes:
            ref_str = convert_nodes_to_str(ref_nodes)
            references = [ref_str]
            if split_comma:
                references = ref_str.split(",")
            return [RefNode(references)]
        return []

    return ref_handler


def hyperref_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    ref_nodes = parser.parse_bracket_as_nodes()
    parser.skip_whitespace()
    title_nodes = parser.parse_brace_as_nodes()
    if ref_nodes:
        ref_str = convert_nodes_to_str(ref_nodes)
        title_str = convert_nodes_to_str(title_nodes)
        return [RefNode(ref_str, title=title_str)]
    return []


REF_COMMANDS = ["ref", "autoref", "eqref", "pageref", "cref", "Cref"]

CITE_COMMANDS = [
    "cite",
    "citep",
    "citet",
    "cites",
    "citealt",
    "citealp",
    "citeauthor",
    "citenum",
    "citeyear",
    "citeyearpar",
    "citefullauthor",
]


def register_ref_label_handlers(parser: ParserCore):
    # labels
    parser.register_handler("label", label_handler)

    # refs
    for command in REF_COMMANDS:
        split_command = command.lower() == "cref"
        parser.register_handler(command, make_ref_handler(split_command))

    # hyperref
    parser.register_handler("hyperref", hyperref_handler)

    # cite
    for command in CITE_COMMANDS:
        handler = make_generic_command_handler(command, "[[{")
        parser.register_handler(command, handler)

    # # citealias
    # for command in ["citetalias", "citepalias"]:
    #     parser.register_handler(command, make_generic_command_handler(command, "{"))
