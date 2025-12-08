"""Unified file resolution logic for all file types."""

import os
from typing import Optional, List


def resolve_file_path(
    file_path: str,
    cwd: str,
    project_root: str,
    extensions: Optional[List[str]] = None,
    extra_search_paths: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Resolve a file path by checking multiple locations.

    Resolution order:
    1. Absolute paths (if file_path is absolute)
    2. Relative to cwd
    3. Relative to extra_search_paths (if provided), resolved from cwd
    4. Relative to project_root (if different from cwd)
    5. Relative to extra_search_paths (if provided), resolved from project_root

    Args:
        file_path: The file path to resolve
        cwd: Current working directory
        project_root: Project root directory
        extensions: List of extensions to try (e.g., [".tex", ".ltx"])
        extra_search_paths: Additional directories to search (e.g., graphics_paths)

    Returns:
        Absolute path to the resolved file, or None if not found
    """
    if extensions is None:
        extensions = []

    def try_resolve_with_extension(path: str) -> Optional[str]:
        """Try to resolve a path with or without extensions."""
        # Try as-is first
        if os.path.isfile(path):
            return os.path.abspath(path)

        # Try with extensions
        for ext in extensions:
            if os.path.isfile(path + ext):
                return os.path.abspath(path + ext)

        return None

    # If absolute path, resolve directly
    if os.path.isabs(file_path):
        return try_resolve_with_extension(file_path)

    # Try relative to cwd first (most common case)
    cwd_path = os.path.join(cwd, file_path)
    result = try_resolve_with_extension(cwd_path)
    if result:
        return result

    # Try extra search paths relative to cwd
    if extra_search_paths:
        for search_path in extra_search_paths:
            candidate = os.path.join(cwd, search_path, file_path)
            result = try_resolve_with_extension(candidate)
            if result:
                return result

    # Fallback: try relative to project_root if different from cwd
    if project_root != cwd:
        root_path = os.path.join(project_root, file_path)
        result = try_resolve_with_extension(root_path)
        if result:
            return result

        # Try extra search paths relative to project_root
        if extra_search_paths:
            for search_path in extra_search_paths:
                candidate = os.path.join(project_root, search_path, file_path)
                result = try_resolve_with_extension(candidate)
                if result:
                    return result

    return None


def make_relative_to_project_root(abs_path: str, project_root: str) -> str:
    """
    Convert an absolute path to be relative to project_root.

    If the path is within project_root, returns a relative path.
    Otherwise, returns the absolute path.

    Args:
        abs_path: Absolute path to convert
        project_root: Project root directory

    Returns:
        Path relative to project_root, or absolute path if outside project_root
    """
    abs_path = os.path.abspath(abs_path)
    abs_project_root = os.path.abspath(project_root)

    try:
        rel_path = os.path.relpath(abs_path, abs_project_root)
        # If path starts with "..", it's outside project_root, keep it absolute
        if not rel_path.startswith('..'):
            return rel_path
    except ValueError:
        # On Windows, relpath raises ValueError if paths are on different drives
        pass

    return abs_path
