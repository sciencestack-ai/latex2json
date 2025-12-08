from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def subfile_handler(expander: ExpanderCore, token: Token):
    r"""Handle \subfile{path/file.tex}

    Loads and processes a subfile, which is typically a standalone LaTeX document
    that can also be included in a main document. The file is processed with the
    current expander state (sharing counters, macros, etc.).

    This is crucial for maintaining counter continuity - if subfiles were handled
    at the parser level, counters would not progress sequentially.
    """
    expander.skip_whitespace()

    # Parse the filename
    subfile_name = expander.parse_brace_name()
    if not subfile_name:
        expander.logger.warning("No file provided for \\subfile")
        return []

    subfile_name = subfile_name.strip()

    expander.logger.info(f"Processing subfile: {subfile_name}")

    # Push the subfile for expansion, similar to \input
    # This maintains the current expander state including counters
    expander.push_file(subfile_name)

    return []


def register_subfile_handlers(expander: ExpanderCore):
    r"""Register \subfile handler."""
    expander.register_handler("subfile", subfile_handler, is_global=True)
