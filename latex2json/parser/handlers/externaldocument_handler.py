from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token


def externaldocument_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    prefix_nodes = parser.parse_bracket_as_nodes()
    parser.skip_whitespace()
    ext_file = parser.parse_brace_name()
    if not ext_file or not prefix_nodes:
        # parser.logger.warning("\\externaldocument expects a file path")
        return None

    prefix_str = parser.convert_nodes_to_str(prefix_nodes)
    parser.register_external_document_prefix(ext_file, prefix_str)

    return []


def register_externaldocument_handler(parser: ParserCore):
    r"""Register \externaldocument handler for cross-document references."""
    parser.register_handler("externaldocument", externaldocument_handler)


