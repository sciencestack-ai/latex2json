from typing import List, Optional
from latex2json.nodes import (
    IncludeGraphicsNode,
    IncludePdfNode,
)
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token
from latex2json.utils.file_resolver import (
    resolve_file_path,
    make_relative_to_project_root,
    get_search_base_from_source,
)
import re
import os

from latex2json.tokens.utils import is_begin_group_token, is_end_group_token


def sanitize_path_str(path_str: str) -> str:
    return (
        path_str.strip()
        .replace('"', "")
        .replace("'", "")
        .replace("{", "")
        .replace("}", "")
    )


def resolve_graphics_path(
    parser: ParserCore, path_str: str, source_file: Optional[str] = None
) -> str:
    """
    Resolve graphics path and return it relative to project_root.

    Resolution order:
    1. Relative to source file's directory
    2. In graphics_paths (relative to source file's directory)
    3. Relative to project_root
    4. In graphics_paths (relative to project_root)

    Returns path relative to project_root (or original if not found)
    """
    # Common image extensions that LaTeX uses
    common_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".eps", ".ps"]

    # Determine search directory from source file context
    search_dir = get_search_base_from_source(
        source_file, parser.project_root, parser.cwd
    )

    # Convert graphics_paths set to list
    extra_paths = list(parser.graphics_paths) if parser.graphics_paths else None

    # Try to resolve the file
    resolved_abs = resolve_file_path(
        path_str,
        cwd=search_dir,
        project_root=parser.project_root,
        extensions=common_extensions,
        extra_search_paths=extra_paths,
    )

    if resolved_abs:
        # Convert to path relative to project_root
        path_str = make_relative_to_project_root(resolved_abs, parser.project_root)

    # Return original path if nothing found (file may not exist yet)
    return sanitize_path_str(path_str)


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

    # Strip quotes from path if present (LaTeX allows quoted filenames)
    path_str = sanitize_path_str(path_str)

    # Get source file from token if available
    source_file = getattr(token, "source_file", None)

    # Resolve path using graphics_paths if needed
    resolved_path = resolve_graphics_path(parser, path_str, source_file=source_file)

    page = None
    if page_str:
        page_match = re.search(r"page=(\d+)", page_str)
        page = int(page_match.group(1)) if page_match else None
    return [IncludeGraphicsNode(resolved_path, page=page)]


def adjustimage_handler(parser: ParserCore, token: Token):
    # simply treat like includegraphics
    r"""\adjustimage{height=0.65cm,valign=m}{figure/panorama_cp0.png}"""
    parser.skip_whitespace()
    options_nodes = parser.parse_brace_as_nodes()

    return includegraphics_handler(parser, token)


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

    # Strip quotes from path if present (LaTeX allows quoted filenames)
    path_str = sanitize_path_str(path_str)

    pages = None
    if pages_str:
        # Match pages parameter with various formats:
        # pages=1, pages={1}, pages=1-5, pages=1-last, pages={1-3,5-last}
        # Use word boundaries to avoid capturing other parameters
        pages_match = re.search(
            r"pages=(?:{([0-9\-,a-z]+)}|([0-9\-,a-z]+)(?=\s|,|$))", pages_str
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


def includestandalone_handler(parser: ParserCore, token: Token):
    """
    Handle \\includestandalone[mode=...]{filename}

    Modes:
    - 'tex' (default): Parse the .tex source file and return its nodes
    - 'image': Use the compiled image file (return IncludeGraphicsNode)
    - 'image|tex': Use image if available, otherwise parse tex source
    """
    parser.skip_whitespace()
    options_nodes = parser.parse_bracket_as_nodes()
    options_str = parser.convert_nodes_to_str(options_nodes) if options_nodes else None

    parser.skip_whitespace()
    path = parser.parse_brace_as_nodes()
    if path is None:
        parser.logger.warning(f"\\includestandalone: Missing path")
        return None
    path_str = parser.convert_nodes_to_str(path)

    # Strip quotes from path
    path_str = path_str.strip().replace('"', "").replace("'", "")

    # Parse mode option (default is 'tex')
    mode = "tex"
    if options_str:
        mode_match = re.search(r"mode\s*=\s*([a-z|]+)", options_str)
        if mode_match:
            mode = mode_match.group(1)

    # Handle different modes
    if mode == "image":
        # Use compiled image file
        resolved_path = resolve_graphics_path(parser, path_str)
        return [IncludeGraphicsNode(resolved_path)]

    elif mode == "image|tex":
        # Try image first, fall back to tex
        resolved_path = resolve_graphics_path(parser, path_str)
        abs_path = parser.get_cwd_path(resolved_path)

        # Check if image exists (with common extensions)
        image_exists = False
        if os.path.isfile(abs_path):
            image_exists = True
        else:
            for ext in [".pdf", ".png", ".jpg", ".jpeg"]:
                if os.path.isfile(abs_path + ext):
                    image_exists = True
                    break

        if image_exists:
            return [IncludeGraphicsNode(resolved_path)]
        # Fall through to tex mode

    # mode == "tex" or fallback from "image|tex"
    # Create standalone parser for isolated processing
    parser2 = parser.create_standalone(logger=parser.logger)

    # Add .tex extension if not present
    if not path_str.endswith(".tex"):
        path_str = path_str + ".tex"

    # Get full filepath and parse
    file_path = os.path.abspath(parser.get_cwd_path(path_str))
    nodes = parser2.parse_file(file_path)

    return nodes if nodes else []


def register_includegraphics_pdf_handlers(parser: ParserCore):
    for includegraphics_cmd in ["includegraphics", "adjincludegraphics", "epsffile"]:
        parser.register_handler(includegraphics_cmd, includegraphics_handler)
    parser.register_handler("adjustimage", adjustimage_handler)

    parser.register_handler("includepdf", includepdf_handler)
    parser.register_handler("includestandalone", includestandalone_handler)

    parser.register_handler("graphicspath", graphicspath_handler)


if __name__ == "__main__":
    from latex2json.parser.parser import Parser

    parser = Parser()
    text = r"""
\includepdf[%
pages=-,% einzubindende Seite aus dem PDF-Dokument
scale=0.9,%
addtotoc={%
  6,% einzubindende Seite aus dem PDF-Dokument
  subsection,% Abschnitt
  2,% Tiefe im Inhaltsverzeichnis
  Beispiele Kurvendiskussion,%
  sec:Beispiel für eine Kurvendiskussion rationaler Funktionen% Label-Name
},%
pagecommand={}%
]{figures/Abitur_Q11.pdf}
    """.strip()
    out = parser.parse(text)
    # print(out)
