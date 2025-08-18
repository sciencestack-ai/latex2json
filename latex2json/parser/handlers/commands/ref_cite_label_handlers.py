from typing import List, Optional
from latex2json.nodes import CommandNode, RefNode
from latex2json.nodes.base_nodes import TextNode
from latex2json.nodes.ref_cite_url_nodes import CiteNode, URLNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token


def label_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    label_nodes = parser.parse_brace_as_nodes()
    if not label_nodes:
        # parser.logger.warning("Warning: \\label expects a label")
        return None

    label_str = parser.convert_nodes_to_str(label_nodes)
    parser.register_label(label_str)

    env_node = parser.current_env
    if env_node:
        env_node.labels.append(label_str)
        return []

    return []
    # # if not found, return generic CommandNode
    # return [CommandNode("label", args=[label_nodes])]


def make_ref_handler(split_comma: bool = False):
    def ref_handler(parser: ParserCore, token: Token):
        parser.parse_asterisk()
        parser.skip_whitespace()
        ref_nodes = parser.parse_brace_as_nodes()
        if ref_nodes:
            ref_str = parser.convert_nodes_to_str(ref_nodes, postprocess=False)
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
    title_nodes = parser.parse_brace_as_nodes() or []
    if ref_nodes:
        ref_str = parser.convert_nodes_to_str(ref_nodes, postprocess=False)
        title_nodes = parser.postprocess_nodes(title_nodes)
        return [RefNode([ref_str], title=title_nodes)]
    return []


def cite_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    prenote = parser.parse_bracket_as_nodes()
    postnote = []
    if prenote:
        parser.skip_whitespace()
        postnote = parser.parse_bracket_as_nodes()
        parser.skip_whitespace()
    citation_nodes = parser.parse_brace_as_nodes()
    if citation_nodes is None:
        parser.logger.warning("Warning: \\cite expects a citation")
        return None

    title = []
    if prenote:
        title = prenote
        if postnote:
            title.extend([TextNode(", ")] + postnote)
        title = parser.postprocess_nodes(title)
    cite_str = parser.convert_nodes_to_str(citation_nodes).split(",")
    cite_str = [s.strip() for s in cite_str]
    return [CiteNode(cite_str, title=title)]


REF_COMMANDS = ["ref", "autoref", "eqref", "pageref", "cref", "Cref", "nameref"]

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
    "autocite",
    "parencite",
]


def defcitealias_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    cite_key = parser.parse_brace_as_nodes()
    if not cite_key:
        parser.logger.warning("Warning: \\defcitealias expects a citation key")
        return None
    alias_nodes = parser.parse_brace_as_nodes()
    if not alias_nodes:
        parser.logger.warning("Warning: \\defcitealias expects an alias")
        return None
    cite_key_str = parser.convert_nodes_to_str(cite_key)
    alias_str = parser.convert_nodes_to_str(alias_nodes)
    parser.cite_aliases[cite_key_str] = alias_str
    return []


def citealias_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    cite_key = parser.parse_brace_as_nodes()
    if not cite_key:
        parser.logger.warning("Warning: \\cite[tp]alias expects a citation key")
        return None
    cite_key_str = parser.convert_nodes_to_str(cite_key)
    alias_str = parser.cite_aliases.get(cite_key_str, None)
    title = [TextNode(alias_str)] if alias_str else []
    return [CiteNode([cite_key_str], title=title)]


def make_url_handler(parse_title: bool = False, path_prefix: str = ""):
    def url_handler(parser: ParserCore, token: Token):
        parser.skip_whitespace()
        url_nodes = parser.parse_brace_as_nodes()
        if not url_nodes:
            parser.logger.warning("Warning: \\url expects a URL")
            return None
        url_str = parser.convert_nodes_to_str(url_nodes)
        title = []

        if parse_title:
            parser.skip_whitespace()
            title = parser.parse_brace_as_nodes() or []
            title = parser.postprocess_nodes(title)

        return [URLNode(path_prefix + url_str, title=title)]

    return url_handler


def noeqref_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    parser.parse_brace_as_nodes()
    return []


def register_ref_label_handlers(parser: ParserCore):
    # labels
    parser.register_handler("label", label_handler)

    # refs
    for command in REF_COMMANDS:
        split_comma = command.lower() == "cref"
        parser.register_handler(command, make_ref_handler(split_comma))

    # hyperref
    parser.register_handler("hyperref", hyperref_handler)

    # cite
    for command in CITE_COMMANDS:
        parser.register_handler(command, cite_handler)

    # defcitealias
    parser.register_handler("defcitealias", defcitealias_handler)

    # citealias
    for command in ["citetalias", "citepalias"]:
        parser.register_handler(command, citealias_handler)

    # urls
    for url_command in ["url", "path"]:
        parser.register_handler(url_command, make_url_handler(parse_title=False))
    parser.register_handler("href", make_url_handler(parse_title=True))
    parser.register_handler(
        "doi", make_url_handler(parse_title=False, path_prefix="https://doi.org/")
    )

    parser.register_handler("noeqref", noeqref_handler)


if __name__ == "__main__":
    from latex2json.parser.parser import Parser

    parser = Parser()
    parser.set_text(r"\cites[see][Chapter 4]{sdsds,   ss}")
    out = parser.parse()
