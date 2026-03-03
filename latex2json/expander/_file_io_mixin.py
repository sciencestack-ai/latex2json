"""Mixin providing file I/O operations for ExpanderCore."""

from __future__ import annotations

import os
from typing import Any, List, Optional, TYPE_CHECKING

from latex2json.utils.encoding import read_file
from latex2json.utils.file_resolver import resolve_file_path as util_resolve
from latex2json.utils.tex_utils import strip_latex_comments
from latex2json.tokens import Token

if TYPE_CHECKING:
    from latex2json.expander.expander_core import ExpanderCore


class FileIOMixin:
    """File I/O operations mixed into ExpanderCore."""

    # Valid LaTeX file extensions
    VALID_LATEX_EXTENSIONS = {".tex", ".sty", ".cls", ".ltx", ".dtx"}

    if TYPE_CHECKING:
        cwd: str
        project_root: str
        loaded_packages: set
        loaded_classes: set
        state: Any
        logger: Any

        def push_text(self, text: str, source_file: Optional[str] = None, preprocess_amstex: bool = True) -> None: ...
        def expand_ltx(self, text: str, source_file: Optional[str] = None) -> List[Token]: ...
        def expand_text(self, text: str, source_file: Optional[str] = None) -> List[Token]: ...

    def _normalize_source_path(self, source_file: Optional[str]) -> Optional[str]:
        """Normalize source file path relative to project root."""
        if not source_file:
            return None

        abs_source = os.path.abspath(source_file)
        abs_project_root = os.path.abspath(self.project_root)

        try:
            rel_path = os.path.relpath(abs_source, abs_project_root)
            # Only use relative path if it doesn't go outside project_root
            if not rel_path.startswith(".."):
                return rel_path
        except ValueError:
            pass  # Different drives on Windows

        return abs_source

    def get_cwd_path(self, file_path: str) -> str:
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.cwd, file_path)
        return file_path

    def resolve_file_path(
        self, file_path: str, default_extension: str = ".tex"
    ) -> Optional[str]:
        """
        Resolve a LaTeX file path with extension handling.

        This method now wraps the unified file_resolver utility but maintains
        backward compatibility with the original API.

        Args:
            file_path: The file path to resolve
            default_extension: Default extension to try (default: ".tex")

        Returns:
            Absolute path to the resolved file, or None if not found
        """
        # Convert Path objects to string
        file_path = str(file_path)

        # Build extensions list based on file and default_extension
        ext = os.path.splitext(file_path)[1].lower()

        # If file has valid LaTeX extension, try as-is first, then with default
        if ext in self.VALID_LATEX_EXTENSIONS:
            extensions = [default_extension] if default_extension else []
        # If no extension or invalid extension, try with default extension
        elif not ext or ext not in self.VALID_LATEX_EXTENSIONS:
            extensions = [default_extension] if default_extension else []
        else:
            extensions = []

        # Use the unified resolver
        return util_resolve(
            file_path,
            cwd=self.cwd,
            project_root=self.project_root,
            extensions=extensions,
            extra_search_paths=None,
        )

    def if_file_exists(self, file_path: str, default_extension: str = ".tex") -> bool:
        return self.resolve_file_path(file_path, default_extension) is not None

    def push_file(self, file_path: str, extension: str = ".tex"):
        """Push a file onto the token stream.

        Args:
            file_path: The file path to push
            extension: The default extension to use if file has no extension
        """
        resolved_path = self.resolve_file_path(file_path, extension)

        if resolved_path is None:
            # File doesn't exist, construct path with extension and let read_file handle the error
            file_path = self.get_cwd_path(file_path)
            ext = os.path.splitext(file_path)[1].lower()
            resolved_path = file_path if ext else file_path + extension

        ext = os.path.splitext(resolved_path)[1].lower()

        # Handle package or class files
        if ext == ".sty":
            self.load_package(resolved_path, extension=ext)
            return
        elif ext == ".cls":
            self.load_class(resolved_path, extension=ext)
            return

        # Load regular file
        input_text = self.read_file(resolved_path)
        if input_text is None:
            return
        # ensure to put \n at the end of the file to delimit/split, in case file ends with %
        self.push_text(input_text + "\n", source_file=resolved_path)

    def expand_file(self, file_path: str, is_package_or_class: bool = False):
        # Determine default extension based on file type
        default_ext = ".sty" if is_package_or_class else ".tex"
        resolved_path = self.resolve_file_path(file_path, default_ext)

        if resolved_path is None:
            self.logger.warning(f"Input file {file_path} does not exist")
            return None

        self.logger.info("EXPANDING FILE " + resolved_path)
        input_text = self.read_file(resolved_path)
        if input_text is None:
            return None

        # strip comments to avoid parsing errors since some files may contain
        # comments that can affect the input stream. To investigate at a future date
        input_text = strip_latex_comments(input_text).strip()
        if not input_text:
            return None

        if is_package_or_class:
            return self.expand_ltx(input_text, source_file=resolved_path)

        return self.expand_text(input_text, source_file=resolved_path)

    def read_file(self, file_path: str) -> Optional[str]:
        if not os.path.exists(file_path):
            self.logger.warning(f"Input file {file_path} does not exist")
            return None
        try:
            content = read_file(file_path)
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {e}")
            return None

        return content

    def _load_package_or_class(
        self,
        package_or_class_name: str,
        extension: str,
        is_package: bool,
        read_file=True,
    ) -> Optional[List[Token]]:
        loaded_set = self.loaded_packages if is_package else self.loaded_classes
        if package_or_class_name in loaded_set:
            return None

        package_path = package_or_class_name
        if not package_path.endswith(extension):
            package_path += extension

        # Strip extension and path to just get base name
        base_name = os.path.splitext(os.path.basename(package_or_class_name))[0]
        loaded_set.add(base_name)

        self.logger.debug(f"Loading package/class: {package_path}")

        if read_file and self.if_file_exists(package_path, extension):
            was_in_package_or_class = self.state.in_package_or_class
            self.state.in_package_or_class = True
            # self.push_scope()
            tokens = self.expand_file(package_path, is_package_or_class=True)
            # self.pop_scope()

            self.state.in_package_or_class = was_in_package_or_class

            return tokens

        return None

    def load_package(
        self, package_name: str, read_file=True, extension: Optional[str] = ".sty"
    ):
        return self._load_package_or_class(
            package_name, extension or ".sty", is_package=True, read_file=read_file
        )

    def load_class(
        self, class_name: str, read_file=True, extension: Optional[str] = ".cls"
    ):
        return self._load_package_or_class(
            class_name, extension or ".cls", is_package=False, read_file=read_file
        )
