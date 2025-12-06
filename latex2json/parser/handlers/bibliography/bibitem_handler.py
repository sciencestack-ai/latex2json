from typing import List, Optional
from latex2json.nodes import ASTNode, BibEntryNode, BibliographyNode
from latex2json.nodes.base_nodes import CommandNode, TextNode
from latex2json.nodes.bibliography_nodes import BibType
from latex2json.nodes.utils import split_nodes_by_predicate, strip_whitespace_nodes
from latex2json.parser.handlers.commands.command_handler_utils import (
    register_ignore_handlers_util,
)
from latex2json.parser.parser_core import Macro, ParserCore
from latex2json.tokens.types import EnvironmentStartToken, Token


def bibitem_handler(parser: ParserCore, token: Token) -> List[BibEntryNode]:
    parser.skip_whitespace()
    label = parser.parse_bracket_as_nodes()
    parser.skip_whitespace()
    cite_key_nodes = parser.parse_brace_as_nodes()
    if not cite_key_nodes:
        parser.logger.warning(f"No cite key found for bibitem")
        return []

    cite_key_str = parser.convert_nodes_to_str(cite_key_nodes).strip()
    label_str = parser.convert_nodes_to_str(label).strip() if label else None

    return [
        BibEntryNode(citation_key=cite_key_str, label=label_str, format=BibType.BIBITEM)
    ]


def split_into_bibitems(nodes: List[ASTNode]) -> List[BibEntryNode]:
    out_items: List[BibEntryNode] = []

    buffer: List[ASTNode] = []
    for node in nodes:
        if isinstance(node, BibEntryNode):
            if out_items:
                out_items[-1].set_body(strip_whitespace_nodes(buffer))
                buffer = []
            out_items.append(node)
        else:
            if isinstance(node, CommandNode) and node.name == "bysame":
                default_str = "-----"
                if len(out_items) > 1:
                    # get previous author(s)
                    prev_bib = out_items[-2]
                    author_str = prev_bib.get_author_str()
                    if author_str:
                        default_str = author_str
                buffer.append(TextNode(default_str))
            else:
                buffer.append(node)

    if buffer and out_items:
        out_items[-1].set_body(strip_whitespace_nodes(buffer))
        buffer = []

    return out_items


def bibliography_handler(
    parser: ParserCore, token: EnvironmentStartToken
) -> List[BibliographyNode]:
    # parse as generic environment first
    out = parser.parse_environment(token)
    if not out:
        return []

    env_nodes: List[ASTNode] = out.body
    items = split_into_bibitems(env_nodes)

    biblio_node = BibliographyNode(items)
    # re-assign labels from environment node
    biblio_node.labels = out.labels

    return [biblio_node]


def natexlab_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
    parser.skip_whitespace()
    label = parser.parse_brace_name()
    if not label:
        return []

    return [TextNode(label)]


def register_bibitem_handler(parser: ParserCore):
    parser.register_handler("bibitem", bibitem_handler)
    parser.register_handler("newblock", lambda parser, token: [])
    parser.register_env_handler("thebibliography", bibliography_handler)
    parser.register_handler("natexlab", natexlab_handler)

    ignore_patterns = {
        # macro provided by the AMS document classes/packages, e.g. Mathematical Reviews MR
        "MR": "{",
        "zbl": "{",
        "mrev": "{",
        "arx": "{",
        "urldef": 0,
        "tempurl": 0,
    }

    register_ignore_handlers_util(parser, ignore_patterns)


if __name__ == "__main__":
    from latex2json.parser import Parser

    text = r"""
    \begin{thebibliography}{99}
		\bibitem[MelRose 2001\natexlab{a}]{Melrosenotes}
		Richard~B. Melrose, \emph{Differential analysis on manifolds with corners},
		Book in preparation.
		
		\bibitem{calculus}
		\bysame, \emph{Calculus of conormal distributions on manifolds with corners},
		Internat. Math. Res. Notices (1992), no.~3, 51--61. % \MR{1154213}
		

    \end{thebibliography}
    """.strip()

    parser = Parser()
    out = parser.parse(text, postprocess=True)
    print(out)
