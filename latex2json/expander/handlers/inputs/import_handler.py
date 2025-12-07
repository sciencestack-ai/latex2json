import os
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def import_handler(expander: ExpanderCore, token: Token):
    r"""Handle \import{path/}{file.tex}

    Changes cwd to path/ before loading file, then restores it.
    Path is relative to the current cwd.
    """
    expander.skip_whitespace()

    # Parse the directory path
    import_dir = expander.parse_brace_name()
    if not import_dir:
        expander.logger.warning("No directory provided for \\import")
        return []

    expander.skip_whitespace()

    # Parse the filename
    import_file = expander.parse_brace_name()
    if not import_file:
        expander.logger.warning("No file provided for \\import")
        return []

    import_dir = import_dir.strip()
    import_file = import_file.strip()

    # Resolve the directory path relative to current cwd
    if os.path.isabs(import_dir):
        new_cwd = import_dir
    else:
        new_cwd = os.path.join(expander.cwd, import_dir)
    new_cwd = os.path.normpath(new_cwd)

    expander.logger.info(f"Importing {import_file} from {new_cwd}")

    # Save current cwd
    old_cwd = expander.cwd

    # Change to new directory
    expander.cwd = new_cwd

    # Load the file (it will be resolved relative to new cwd)
    expander.push_file(import_file)

    # Restore old cwd
    expander.cwd = old_cwd

    return []


def subimport_handler(expander: ExpanderCore, token: Token):
    r"""Handle \subimport{path/}{file.tex}

    Like \import, but path is relative to the directory of the current file
    being processed (not the original cwd).
    """
    expander.skip_whitespace()

    # Parse the directory path
    import_dir = expander.parse_brace_name()
    if not import_dir:
        expander.logger.warning("No directory provided for \\subimport")
        return []

    expander.skip_whitespace()

    # Parse the filename
    import_file = expander.parse_brace_name()
    if not import_file:
        expander.logger.warning("No file provided for \\subimport")
        return []

    import_dir = import_dir.strip()
    import_file = import_file.strip()

    # Get current file's directory from the token stream
    # The current source file is the last one in the stream
    current_file = expander.stream.get_current_source_file()

    if current_file:
        # Convert to absolute path
        if os.path.isabs(current_file):
            current_file_abs = current_file
        else:
            # Relative paths are now relative to project_root
            current_file_abs = os.path.join(expander.project_root, current_file)

        current_file_dir = os.path.dirname(os.path.abspath(current_file_abs))
    else:
        # Fallback to cwd if no source file info
        current_file_dir = expander.cwd

    expander.logger.debug(f"Subimport: current file: {current_file}, resolved dir: {current_file_dir}")

    # Resolve the directory path relative to current file's directory
    if os.path.isabs(import_dir):
        new_cwd = import_dir
    else:
        new_cwd = os.path.join(current_file_dir, import_dir)
    new_cwd = os.path.normpath(new_cwd)

    expander.logger.info(f"Subimporting {import_file} from {new_cwd} (relative to {current_file_dir})")

    # Save current cwd
    old_cwd = expander.cwd

    # Change to new directory
    expander.cwd = new_cwd

    # Load the file (it will be resolved relative to new cwd)
    expander.push_file(import_file)

    # Restore old cwd
    expander.cwd = old_cwd

    return []


def register_import_handlers(expander: ExpanderCore):
    r"""Register \import and \subimport handlers."""
    expander.register_handler("import", import_handler, is_global=True)
    expander.register_handler("subimport", subimport_handler, is_global=True)
