import os
from latex2json.expander.expander import Expander
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token


def create_subfile_parser(parser: ParserCore) -> ParserCore:
    # create standalone parser + fresh expander (to mimic subfiles as standalone documents)
    # however, we share the counter manager state in order to share/progress the same counters (hack?)
    expander = Expander()

    parser2 = parser.create_standalone(logger=parser.logger, expander=expander)
    # share counter manager state
    # share expander state??
    parser2.expander.state = parser.expander.state

    # share same label registry to assign labels to respective filenames
    parser2.label_registry = parser.label_registry
    parser2.external_documents_prefixes = parser.external_documents_prefixes
    # disable standalone mode since subfiles must be fully parsed and has expansions etc
    parser2.standalone_mode = False

    return parser2


def subfile_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    file_name = parser.parse_brace_name()
    if not file_name:
        parser.logger.warning("\\subfile expects a file path")
        return None

    # create standalone parser + fresh expander (to mimic subfiles as standalone documents)
    parser2 = create_subfile_parser(parser)

    # get full filepath
    file_path = os.path.abspath(parser.get_cwd_path(file_name))
    # parse file into nodes
    nodes = parser2.parse_file(file_path)

    return nodes


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


def register_subfile_handlers(parser: ParserCore):
    parser.register_handler("subfile", subfile_handler)

    # externaldocument
    parser.register_handler("externaldocument", externaldocument_handler)


if __name__ == "__main__":
    from latex2json.parser.parser import Parser

    from typing import List
    from latex2json.nodes.utils import find_nodes_by_type
    from latex2json.nodes.ref_cite_url_nodes import RefNode

    from logging import Logger, DEBUG, StreamHandler, INFO

    logger = Logger("test")
    # Add a handler to output to console
    handler = StreamHandler()
    handler.setLevel(INFO)
    logger.addHandler(handler)

    parser = Parser(logger=logger)
    register_subfile_handlers(parser)

    # main file
    filepath = (
        "/Users/cj/Documents/python/latex2json/tests/samples/subfiles/manuscript.tex"
    )
    nodes = parser.parse_file(
        filepath, postprocess=True, resolve_cross_document_references=True
    )

    ref_nodes: List[RefNode] = find_nodes_by_type(nodes, RefNode)
    for ref_node in ref_nodes:
        print(ref_node.references, ref_node.source_file)
