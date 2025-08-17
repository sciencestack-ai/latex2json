from typing import List
from latex2json.expander.expander import Expander
from latex2json.nodes.base_nodes import ASTNode
from latex2json.nodes.ref_cite_url_nodes import RefNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token
import os


def find_ref_nodes(nodes: List[ASTNode]) -> List[RefNode]:
    ref_nodes: List[RefNode] = []
    for node in nodes:
        if isinstance(node, RefNode):
            ref_nodes.append(node)
        elif node.children:
            ref_nodes.extend(find_ref_nodes(node.children))
    return ref_nodes


def subfile_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    file_name = parser.parse_brace_name()
    if not file_name:
        parser.logger.warning("Warning: \\subfile expects a file path")
        return None

    # create standalone parser + fresh expander (to mimic subfiles as standalone documents)
    # however, we share the counter manager state in order to share/progress the same counters (hack?)
    expander = Expander()
    expander.state.counter_manager = parser.expander.state.counter_manager

    parser2 = parser.create_standalone(logger=parser.logger, expander=expander)
    # disable standalone mode since we treat it as if this subfile is a standalone document that can be fully parsed and has expansions etc
    parser2.standalone_mode = False

    # get full filepath
    file_path = os.path.abspath(parser.get_cwd_path(file_name))
    # parse file into nodes
    nodes = parser2.parse_file(file_path)

    # recurse through the nodes and look for all referencenodes.
    ref_nodes = find_ref_nodes(nodes)
    # print(ref_nodes)
    # print(parser2.external_documents_prefixes)
    # print(parser2.filename, parser.filename)

    prefix_to_external_documents = {
        v: k for k, v in parser2.external_documents_prefixes.items()
    }

    # then do reference resolution:
    # match the reference nodes to parser2.external_documents based on parser.filename.
    for ref_node in ref_nodes:
        for i, ref in enumerate(ref_node.references):
            is_external_ref = False
            for k, v in prefix_to_external_documents.items():
                if ref.startswith(k):
                    # found prefix. Strip it out?
                    print("FOUND", ref, "PREFIX", k)
                    ref_node.references[i] = ref.lstrip(k)
                    is_external_ref = True
                    break
            if not is_external_ref:
                # convert the local references + labels?
                print("LOCAL", ref)
                pass

    return nodes


def externaldocument_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    prefix_nodes = parser.parse_bracket_as_nodes()
    parser.skip_whitespace()
    ext_file = parser.parse_brace_name()
    if not ext_file or not prefix_nodes:
        # parser.logger.warning("Warning: \\externaldocument expects a file path")
        return None

    prefix_str = parser.convert_nodes_to_str(prefix_nodes)
    parser.external_documents_prefixes[ext_file.strip()] = prefix_str

    return []


def register_subfile_handlers(parser: ParserCore):
    parser.register_handler("subfile", subfile_handler)

    # externaldocument
    parser.register_handler("externaldocument", externaldocument_handler)


if __name__ == "__main__":
    from latex2json.parser.parser import Parser
    from logging import Logger, DEBUG, StreamHandler, INFO

    logger = Logger("test")
    # Add a handler to output to console
    handler = StreamHandler()
    handler.setLevel(INFO)
    logger.addHandler(handler)

    parser = Parser(logger=logger)
    register_subfile_handlers(parser)

    #     text = r"""
    #     \externaldocument[M-]{manuscript}

    #     \section{Test}
    #     \ref{M-lem:a}
    # """.strip()
    #     nodes = parser.parse(text)
    #     print(parser.external_documents_prefixes)

    # main file
    filepath = (
        "/Users/cj/Documents/python/latex2json/tests/samples/subfiles/manuscript.tex"
    )
    nodes = parser.parse_file(filepath)
