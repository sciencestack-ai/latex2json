from typing import List, Optional
from latex2json.nodes import (
    IncludeGraphicsNode,
    IncludePdfNode,
)
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token
import re
import os

from latex2json.tokens.utils import is_begin_group_token, is_end_group_token


def resolve_graphics_path(parser: ParserCore, path_str: str) -> str:
    """
    Resolve graphics path by checking:
    1. The path itself (relative to parser.cwd or absolute)
    2. If not found, check in graphics_paths directories (relative to parser.cwd)

    Returns the resolved path (or original if no resolution needed/possible)
    """
    # Common image extensions that LaTeX uses
    common_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".eps", ".ps"]

    def check_cwd_path_exists(relative_path: str) -> bool:
        """Check if file exists (relative to cwd) with or without common extensions"""
        abs_path = parser.get_cwd_path(relative_path)
        if os.path.isfile(abs_path):
            return True
        # Try adding common extensions if no extension provided
        if not os.path.splitext(abs_path)[1]:
            for ext in common_extensions:
                if os.path.isfile(abs_path + ext):
                    return True
        return False

    # First, check the direct path
    if check_cwd_path_exists(path_str):
        return path_str

    # If not found and we have graphics_paths, try each one
    if parser.graphics_paths:
        for graphics_dir in parser.graphics_paths:
            candidate_path = os.path.join(graphics_dir, path_str)
            if check_cwd_path_exists(candidate_path):
                return candidate_path

    # Return original path if nothing found (file may not exist yet or be relative)
    return path_str


def includegraphics_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    page_nodes = parser.parse_bracket_as_nodes()
    page_str = parser.convert_nodes_to_str(page_nodes) if page_nodes else None
    parser.skip_whitespace()
    path = parser.parse_brace_as_nodes()
    if path is None:
        parser.logger.warning(f"\\includegraphics: Missing path")
        return None
    path_str = parser.convert_nodes_to_str(path)

    # Resolve path using graphics_paths if needed
    resolved_path = resolve_graphics_path(parser, path_str)

    page = None
    if page_str:
        page_match = re.search(r"page=(\d+)", page_str)
        page = int(page_match.group(1)) if page_match else None
    return [IncludeGraphicsNode(resolved_path, page=page)]


def includepdf_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    pages_nodes = parser.parse_bracket_as_nodes()
    pages_str = parser.convert_nodes_to_str(pages_nodes) if pages_nodes else None
    parser.skip_whitespace()
    path = parser.parse_brace_as_nodes()
    if path is None:
        parser.logger.warning(f"\\includepdf: Missing path")
        return None
    path_str = parser.convert_nodes_to_str(path)

    pages = None
    if pages_str:
        # Match pages parameter with various formats:
        # pages=1, pages={1}, pages=1-5, pages=1-last, pages={1-3,5-last}
        pages_match = re.search(
            r"pages=(?:{([0-9\-,a-zA-Z]+)}|([0-9\-,a-zA-Z]+))", pages_str
        )
        # Use first non-None group (either braced or unbraced match)
        pages = (
            next((g for g in pages_match.groups() if g is not None), None)
            if pages_match
            else None
        )
    return [IncludePdfNode(path_str, pages=pages)]


def graphicspath_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    path_tokens = parser.parse_begin_end_as_tokens(
        begin_predicate=is_begin_group_token,
        end_predicate=is_end_group_token,
        check_first_token=True,
        include_begin_end_tokens=False,
    )
    if not path_tokens:
        return []
    # e.g. '{', 'f', 'i', 'g', 'u', 'r', 'e', 's', '/', '}', '{', 'i', 'm', 'a', 'g', 'e', 's', '/', '}'
    # Split by braces to extract individual paths
    paths: List[str] = []
    current_path: List[Token] = []
    depth = 0

    for tok in path_tokens:
        if is_begin_group_token(tok):
            if depth > 0:
                current_path.append(tok)
            depth += 1
        elif is_end_group_token(tok):
            depth -= 1
            if depth == 0:
                # End of a path, convert tokens to string
                if current_path:
                    path_str = parser.convert_tokens_to_str(current_path).strip()
                    paths.append(path_str)
                    current_path = []
            else:
                current_path.append(tok)
        else:
            if depth > 0:
                current_path.append(tok)

    if paths:
        parser.graphics_paths.update(paths)

    return []


def register_includegraphics_pdf_handlers(parser: ParserCore):
    parser.register_handler("includegraphics", includegraphics_handler)
    parser.register_handler("includepdf", includepdf_handler)

    parser.register_handler("graphicspath", graphicspath_handler)


if __name__ == "__main__":
    from latex2json.parser.parser import Parser

    parser = Parser()
    text = r"""
    \graphicspath{{figures/}{images/}}
    \includegraphics[width=0.45\linewidth, page=3]{figures.pdf}
    """.strip()
    out = parser.parse(text)
    # print(out)
