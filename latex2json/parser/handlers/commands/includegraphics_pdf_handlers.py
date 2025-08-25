from latex2json.nodes import (
    IncludeGraphicsNode,
    IncludePdfNode,
)
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token
import re


def includegraphics_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    page_nodes = parser.parse_bracket_as_nodes()
    page_str = parser.convert_nodes_to_str(page_nodes) if page_nodes else None
    parser.skip_whitespace()
    path = parser.parse_brace_as_nodes()
    if path is None:
        parser.logger.warning(f"Warning: \\includegraphics: Missing path")
        return None
    path_str = parser.convert_nodes_to_str(path)

    page = None
    if page_str:
        page_match = re.search(r"page=(\d+)", page_str)
        page = int(page_match.group(1)) if page_match else None
    return [IncludeGraphicsNode(path_str, page=page)]


def includepdf_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    pages_nodes = parser.parse_bracket_as_nodes()
    pages_str = parser.convert_nodes_to_str(pages_nodes) if pages_nodes else None
    parser.skip_whitespace()
    path = parser.parse_brace_as_nodes()
    if path is None:
        parser.logger.warning(f"Warning: \\includepdf: Missing path")
        return None
    path_str = parser.convert_nodes_to_str(path)

    pages = None
    if pages_str:
        pages_match = re.search(r"pages=(?:{([0-9-,]+)}|([0-9-,]+))", pages_str)
        # Use first non-None group (either braced or unbraced match)
        pages = (
            next((g for g in pages_match.groups() if g is not None), None)
            if pages_match
            else None
        )
    return [IncludePdfNode(path_str, pages=pages)]


def graphicspath_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    path = parser.parse_brace_as_nodes()
    # ignore??
    return []


def register_includegraphics_pdf_handlers(parser: ParserCore):
    for graphics in ["includegraphics", "epsfbox"]:
        parser.register_handler(graphics, includegraphics_handler)
    parser.register_handler("includepdf", includepdf_handler)

    parser.register_handler("graphicspath", graphicspath_handler)


if __name__ == "__main__":
    from latex2json.parser.parser import Parser

    parser = Parser()
    text = r"""
    \includegraphics[page=1]{example.pdf}
    \includepdf[pages=1]{example.pdf}
    """.strip()
    out = parser.parse(text)
    # print(out)
