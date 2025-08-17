from latex2json.expander.expander import Expander
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token
import os


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
    # get full filepath
    file_path = os.path.abspath(parser.get_cwd_path(file_name))
    # parse file into nodes
    nodes = parser2.parse_file(file_path)
    # then do reference resolution:
    # iterate through the nodes and look for all referencenodes.
    # then match the reference nodes to parser2.external_documents based on parser.filename.
    # if prefix detected and match parser.registry references, strip the prefix
    # for all others, convert the local references + labels?

    return nodes


def externaldocument_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    prefix_nodes = parser.parse_bracket_as_nodes()
    parser.skip_whitespace()
    ext_file = parser.parse_brace_name()
    if not ext_file or not prefix_nodes:
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

    parser = Parser()

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
