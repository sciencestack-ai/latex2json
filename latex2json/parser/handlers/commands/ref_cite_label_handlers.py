from typing import List, Optional
from latex2json.latex_maps.url_commands import URL_COMMANDS
from latex2json.nodes import CommandNode, RefNode
from latex2json.nodes.base_nodes import TextNode
from latex2json.nodes.ref_cite_url_nodes import CiteNode, URLNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token


def label_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    label_nodes = parser.parse_brace_as_nodes()
    if not label_nodes:
        # parser.logger.warning("\\label expects a label")
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


def hypertarget_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    anchor_node = parser.parse_brace_as_nodes()
    anchor_id = parser.convert_nodes_to_str(anchor_node)
    parser.skip_whitespace()
    title_nodes = parser.parse_brace_as_nodes()
    if not anchor_id:
        return []
    parser.register_label(anchor_id)
    if not title_nodes:
        # if empty, default as \label{anchor_id}
        env_node = parser.current_env
        if env_node:
            env_node.labels.append(anchor_id)
        return []

    # just append the label to the first node?
    title_nodes[0].labels.append(anchor_id)
    return title_nodes


def hyperlink_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    anchor_node = parser.parse_brace_as_nodes()
    anchor_id = parser.convert_nodes_to_str(anchor_node)
    parser.skip_whitespace()
    title_nodes = parser.parse_brace_as_nodes() or []
    title_nodes = parser.postprocess_nodes(title_nodes)
    if not anchor_id:
        return []
    # if anchor_id.startswith("cite."):
    #     cite_key = anchor_id.split(".")[1]
    #     return [CiteNode([cite_key], title=title_nodes)]
    return [RefNode([anchor_id], title=title_nodes)]


def cite_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    prenote = parser.parse_bracket_as_nodes()
    postnote = []
    if prenote is not None:
        parser.skip_whitespace()
        postnote = parser.parse_bracket_as_nodes()
        parser.skip_whitespace()
    citation_nodes = parser.parse_brace_as_nodes()
    if citation_nodes is None:
        parser.logger.warning(
            f"\\cite expects a citation, found {parser.peek()} instead"
        )
        return None

    title = []
    if prenote:
        title = prenote
        if postnote:
            title.extend([TextNode(", ")] + postnote)
        title = parser.postprocess_nodes(title)
    cite_str = parser.convert_nodes_to_str(citation_nodes).split(",")
    cite_str = [s.strip() for s in cite_str]

    # Track all citation keys
    for cite_key in cite_str:
        if cite_key:  # Skip empty strings
            parser.register_citation(cite_key)

    return [CiteNode(cite_str, title=title)]


REF_COMMANDS = [
    "ref",
    "autoref",
    "eqref",
    "pageref",
    "cref",
    "Cref",
    "nameref",
    "subref",
    "equationref",
    "sectionref",
    "appendixref",
    "figureref",
    "tableref",
]

CITE_COMMANDS = [
    "cite",
    "shortcite",
    "citep",
    "citet",
    "Citet",
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
    "onlinecite",
]


def crefalias_handler(parser: ParserCore, token: Token):
    """Handler for \\crefalias from cleveref package.
    Syntax: \\crefalias{counter}{type}
    Maps a counter name to a reference type for cross-referencing."""
    parser.skip_whitespace()
    counter_nodes = parser.parse_brace_as_nodes()
    parser.skip_whitespace()
    type_nodes = parser.parse_brace_as_nodes()
    if not counter_nodes:
        parser.logger.warning("\\crefalias expects a counter name")
        return None
    if not type_nodes:
        parser.logger.warning("\\crefalias expects a type name")
        return None
    # For this parser, we don't need to track counter aliases
    # as we're extracting semantic content, not rendering references
    # Just consume the command and return empty
    return []


def defcitealias_handler(parser: ParserCore, token: Token):
    """Handler for \\defcitealias from natbib package.
    Syntax: \\defcitealias{key}{alias}
    Defines a citation alias for bibliography entries."""
    parser.skip_whitespace()
    cite_key = parser.parse_brace_as_nodes()
    parser.skip_whitespace()
    alias_nodes = parser.parse_brace_as_nodes()
    if not cite_key:
        parser.logger.warning("\\defcitealias expects a citation key")
        return None
    if not alias_nodes:
        parser.logger.warning("\\defcitealias expects an alias")
        return None
    cite_key_str = parser.convert_nodes_to_str(cite_key)
    alias_str = parser.convert_nodes_to_str(alias_nodes)
    parser.cite_aliases[cite_key_str] = alias_str
    return []


def citealias_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    cite_key = parser.parse_brace_as_nodes()
    if not cite_key:
        parser.logger.warning("\\cite[tp]alias expects a citation key")
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
            parser.logger.warning("\\url expects a URL")
            return None
        url_str = parser.convert_nodes_to_str(url_nodes)
        title = []

        if parse_title:
            parser.skip_whitespace()
            title = parser.parse_brace_as_nodes() or []
            title = parser.postprocess_nodes(title)

        return [URLNode(path_prefix + url_str, title=title)]

    return url_handler


def nocite_handler(parser: ParserCore, token: Token):
    """Handler for \\nocite command.
    Tracks citations but doesn't produce output nodes.
    Note: \\nocite{*} will register '*' as a citation key."""
    parser.skip_whitespace()
    citation_nodes = parser.parse_brace_as_nodes()
    if citation_nodes:
        cite_str = parser.convert_nodes_to_str(citation_nodes).split(",")
        cite_str = [s.strip() for s in cite_str]
        # Track all citation keys
        for cite_key in cite_str:
            if cite_key:
                parser.register_citation(cite_key)
    return []


def noeqref_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    parser.parse_brace_as_nodes()
    return []


def register_ref_label_handlers(parser: ParserCore):
    # labels
    parser.register_handler("label", label_handler)
    # floatconts (from jmlr package). TECHNICALLY floatconts args are \floatconts{label}{caption...}{content...}
    # but we simply treat it for its first arg as a label
    parser.register_handler("floatconts", label_handler)

    # refs
    for command in REF_COMMANDS:
        split_comma = command.lower() == "cref"
        parser.register_handler(command, make_ref_handler(split_comma))

    parser.register_handler("noeqref", noeqref_handler)

    # hypertarget/hyperlink
    parser.register_handler("hypertarget", hypertarget_handler)
    parser.register_handler("hyperlink", hyperlink_handler)

    # hyperref
    parser.register_handler("hyperref", hyperref_handler)

    # cite
    for command in CITE_COMMANDS:
        parser.register_handler(command, cite_handler)

    # nocite (track citations but don't produce output)
    parser.register_handler("nocite", nocite_handler)

    # crefalias (cleveref package)
    parser.register_handler("crefalias", crefalias_handler)

    # defcitealias (natbib package)
    parser.register_handler("defcitealias", defcitealias_handler)

    # citealias
    for command in ["citetalias", "citepalias"]:
        parser.register_handler(command, citealias_handler)

    # urls
    for url_command, spec in URL_COMMANDS.items():
        path_prefix = ""
        if url_command == "doi":
            path_prefix = "https://doi.org/"

        parser.register_handler(
            url_command,
            make_url_handler(parse_title=spec.startswith("["), path_prefix=path_prefix),
        )


if __name__ == "__main__":
    from latex2json.parser.parser import Parser

    text = r"""
    
\hypertarget{cite.WZ25b}{CHANGE MANNN }
\hyperlink{cite.WZ25b}{HOHSAD  }
""".strip()

    parser = Parser()
    out = parser.parse(text)
