from latex2json.nodes.base_nodes import ASTNode
from latex2json.parser.handlers.bibliography.bib_text_utils import (
    extract_nested_content,
)
from latex2json.parser.parser_core import ParserCore
from latex2json.nodes import BibEntryNode, BibliographyNode
from typing import Dict, List
import re

from latex2json.tokens import Token
from latex2json.tokens.types import TokenType
from latex2json.tokens.utils import (
    is_begin_group_token,
    is_end_group_token,
    strip_whitespace_tokens,
)


def parse_bib_fields(entry_content: str) -> Dict[str, str]:
    fields = {}
    if not entry_content:
        return fields

    pos = 0
    while pos < len(entry_content):
        # Find field name
        field_match = re.match(r"\s*(\w+)\s*=\s*", entry_content[pos:])
        if not field_match:
            pos += 1
            continue

        field_name = field_match.group(1).lower()
        field_start = pos + field_match.end()

        # Get value - either in braces or until comma
        if entry_content[field_start:].lstrip().startswith("{"):
            # Skip whitespace to actual brace
            while (
                field_start < len(entry_content)
                and entry_content[field_start].isspace()
            ):
                field_start += 1
            value, value_end = extract_nested_content(entry_content[field_start:])
            if value is not None:
                # Strip any remaining braces from the value
                value = re.sub(r"\{([^}]*)\}", r"\1", value)
                value = value.strip()
                # Handle multiple instances of the same field
                if field_name in fields:
                    fields[field_name] = f"{fields[field_name]} and {value}"
                else:
                    fields[field_name] = value
                pos = field_start + value_end
        else:
            # Handle values until comma
            comma_pos = entry_content.find(",", field_start)
            if comma_pos == -1:
                comma_pos = len(entry_content)
            value = entry_content[field_start:comma_pos].strip()
            # Strip any remaining braces from the value
            value = re.sub(r"\{([^}]*)\}", r"\1", value)
            # Handle multiple instances of the same field
            if field_name in fields:
                fields[field_name] = f"{fields[field_name]} and {value}"
            else:
                fields[field_name] = value
            pos = comma_pos + 1

        # Skip trailing whitespace
        while pos < len(entry_content) and entry_content[pos].isspace():
            pos += 1

    return fields


def bib_handler(parser: ParserCore, token: Token) -> List[BibEntryNode]:
    blocks = parser.parse_braced_blocks(2)
    if len(blocks) != 2:
        parser.logger.warning(f"\\bib block must have 3 arguments")
        return []

    parser.skip_whitespace()
    # parse the 3rd block
    body_tokens = parser.parse_begin_end_as_tokens(
        is_begin_group_token,
        is_end_group_token,
    )

    # parse first argument as cite key
    cite_key = parser.convert_nodes_to_str(blocks[0]).strip()
    if not cite_key:
        parser.logger.warning(f"\\bib block must have a cite key")
        return []

    entry_type = parser.convert_nodes_to_str(blocks[1]).strip()  # e.g. article

    # parse third argument as body
    fields = {}
    if body_tokens:
        body_str = parser.convert_tokens_to_str(body_tokens).strip()
        fields = parse_bib_fields(body_str)

    entry = BibEntryNode.from_bibtex(
        entry_type=entry_type, citation_key=cite_key, fields=fields
    )

    return [entry]


def biblist_handler(parser: ParserCore, token: Token) -> List[BibliographyNode]:
    # parse as generic environment first
    out = parser.parse_environment(token)
    if not out:
        return []

    items = [node for node in out.body if isinstance(node, BibEntryNode)]

    biblio_node = BibliographyNode(items)
    # re-assign labels from environment node
    biblio_node.labels = out.labels

    return [biblio_node]


def bibdiv_handler(parser: ParserCore, token: Token) -> List[BibEntryNode]:
    # parse until end of bibdiv
    # push inner contents back to stack, effectively ignoring this outer bibdiv
    tokens = parser.parse_tokens_until(
        lambda tok: tok == Token(TokenType.ENVIRONMENT_END, "bibdiv"),
        consume_predicate=True,
    )
    parser.push_tokens(strip_whitespace_tokens(tokens))
    return []


def register_bibdiv_handler(parser: ParserCore):
    parser.register_handler("bib", bib_handler)

    parser.register_env_handler("biblist", biblist_handler)
    parser.register_env_handler("bibdiv", bibdiv_handler)


if __name__ == "__main__":
    from latex2json.parser import Parser

    text = r"""
\begin{bibdiv}
\begin{biblist}

\bib{CZN23strip}{article}{
      author={{Coti Zelati}, Michele},
      author={{Nualart}, Marc},
       title={{Explicit solutions and linear inviscid damping in the
  Euler-Boussinesq equation near a stratified Couette flow in the periodic
  strip}},
        date={2023-09},
     journal={arXiv e-prints},
      eprint={2309.08419},
}

\end{biblist}
\end{bibdiv}
"""
    parser = Parser()
    out = parser.parse(text, postprocess=True)
