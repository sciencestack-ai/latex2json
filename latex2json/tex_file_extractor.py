import os
import gzip
import tarfile
import tempfile
import shutil
from typing import List, Optional, Tuple
import zipfile
import re
from contextlib import contextmanager

from latex2json.utils.tex_utils import strip_latex_comments
from latex2json.utils.encoding import read_file

DOCUMENTCLASS_PATTERN = re.compile(
    r"\\documentclass\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}",
    re.DOTALL,
)
BEGIN_DOCUMENT_PATTERN = re.compile(r"\\begin\s*\{document\}|\\document\b", re.DOTALL)


SUPPORTED_TEX_EXTENSIONS = (".tex", ".flt")


class TexFileExtractor:
    """A class to handle reading and processing TeX files from various sources."""

    @staticmethod
    def is_main_tex_file(content: str) -> bool:
        """Check if content contains markers indicating it's a main TeX file.

        Args:
            content (str): The file content to check

        Returns:
            bool: True if the content appears to be a main TeX file
        """
        clean_content = strip_latex_comments(content)
        doc_class_match = DOCUMENTCLASS_PATTERN.search(clean_content)
        if doc_class_match:
            doc_cls = doc_class_match.group(1).strip()
            if "subfiles" in doc_cls.split(","):
                return False
            return True
        if BEGIN_DOCUMENT_PATTERN.search(clean_content):
            return True
        return False

    @staticmethod
    def find_main_tex_file(folder_path: str):
        """Find the main TeX file and its containing folder in a directory or its subdirectories.

        Args:
            folder_path (str): Path to the directory to search

        Returns:
            tuple: (main_tex_file, main_folder)
                  main_tex_file: Relative path to the main TeX file
                  main_folder: Path to the folder containing the main TeX file

        Raises:
            FileNotFoundError: If no main TeX file is found
        """
        all_tex_files: List[Tuple[str, str]] = []
        main_tex_files: List[Tuple[str, str]] = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith(SUPPORTED_TEX_EXTENSIONS):
                    full_path = os.path.join(root, file)
                    base_path = os.path.relpath(full_path, folder_path)
                    all_tex_files.append((base_path, root))
                    try:
                        content = read_file(full_path)
                        if TexFileExtractor.is_main_tex_file(content):
                            main_tex_files.append((base_path, root))
                    except Exception as e:
                        print(f"Error reading {full_path}: {str(e)}")
                        continue
        if len(all_tex_files) == 1:
            # just return the one
            return all_tex_files[0]
        N_main_tex_files = len(main_tex_files)
        if N_main_tex_files == 1:
            return main_tex_files[0]
        elif N_main_tex_files > 1:
            # Prioritize main.tex if it exists
            for base_path, root in main_tex_files:
                if os.path.basename(base_path) == "main.tex":
                    return (base_path, root)
            # Otherwise return the first one
            return main_tex_files[0]

        raise FileNotFoundError(
            "No main TeX file found (no documentclass or begin{document} found)"
        )

    @staticmethod
    @contextmanager
    def process_compressed_file(
        compressed_path: str, temp_dir: Optional[str] = None, cleanup: bool = True
    ):
        """Process a compressed file (gzip, tar.gz, or zip).

        Args:
            compressed_path (str): Path to the compressed file
            cleanup (bool): Whether to clean up temporary files after processing

        Yields:
            tuple: (main_tex_file, main_folder)
                  main_tex_file: Relative path of the main TeX file within the temp dir
                  main_folder: Path to temporary directory containing extracted files
        """
        if not temp_dir:
            temp_dir = tempfile.mkdtemp()
        elif not os.path.isdir(temp_dir):
            # create dir
            try:
                os.makedirs(temp_dir)
            except Exception as e:
                temp_dir = tempfile.mkdtemp()

        main_tex = None
        processed = False

        try:
            if compressed_path.endswith(".zip"):
                with zipfile.ZipFile(compressed_path, "r") as zip_ref:
                    # Security check for unsafe paths before extraction
                    safe_members = []
                    for member in zip_ref.namelist():
                        member_path = os.path.join(temp_dir, member)
                        # Prevent path traversal and absolute paths
                        if (
                            os.path.isabs(member)
                            or ".." in member
                            or not os.path.abspath(member_path).startswith(
                                os.path.abspath(temp_dir)
                            )
                        ):
                            print(
                                f"[WARNING] Skipping potentially unsafe path in zip: {member}"
                            )
                            continue
                        safe_members.append(member)
                    # Extract only safe members
                    for member in safe_members:
                        zip_ref.extract(member, temp_dir)

                main_tex, main_folder_abs = TexFileExtractor.find_main_tex_file(
                    temp_dir
                )
                processed = True

            elif compressed_path.endswith((".tar.gz", ".tgz")):
                try:
                    # Open .tar.gz directly using tarfile
                    with tarfile.open(compressed_path, "r:gz") as tar:
                        # Security check for unsafe paths before extraction
                        safe_members = []
                        for member in tar.getmembers():
                            member_path = os.path.join(temp_dir, member.name)
                            # Prevent path traversal and absolute paths
                            if (
                                os.path.isabs(member.name)
                                or ".." in member.name
                                or not os.path.abspath(member_path).startswith(
                                    os.path.abspath(temp_dir)
                                )
                            ):
                                print(
                                    f"[WARNING] Skipping potentially unsafe path in tar.gz: {member.name}"
                                )
                                continue
                            safe_members.append(member)
                        # Extract only safe members (use filter='data' in Python 3.12+ for better security)
                        # For broader compatibility, we extract member by member after checks
                        for member in safe_members:
                            tar.extract(member, temp_dir)

                    main_tex, main_folder_abs = TexFileExtractor.find_main_tex_file(
                        temp_dir
                    )
                    processed = True
                except (
                    tarfile.ReadError,
                    tarfile.CompressionError,
                    EOFError,
                    gzip.BadGzipFile,
                ) as e:
                    print(
                        f"[INFO] Failed to open {compressed_path} as tar.gz: {e}. Checking if it's a single gzipped file."
                    )
                    # Fall through to check if it's a single .gz file if the extension matches

            # Handle single .gz file (or fallback from failed .tar.gz attempt)
            if not processed and compressed_path.endswith(".gz"):
                try:
                    # Assume it's a single gzipped file
                    base_filename = os.path.basename(compressed_path)
                    # Attempt to create a sensible output filename
                    output_filename = (
                        base_filename[:-3]
                        if base_filename.lower().endswith(".gz")
                        else base_filename + "_extracted"
                    )
                    if not output_filename.lower().endswith(SUPPORTED_TEX_EXTENSIONS):
                        output_filename += ".tex"  # Assume .tex if no extension
                    temp_file_path = os.path.join(temp_dir, output_filename)

                    with gzip.open(compressed_path, "rb") as f_in, open(
                        temp_file_path, "wb"
                    ) as f_out:
                        shutil.copyfileobj(f_in, f_out)

                    main_tex = output_filename
                    main_folder_abs = temp_dir
                    processed = True
                    # content_str = read_file(temp_file_path)
                    # if TexFileExtractor.is_main_tex_file(content_str):
                    #     # For single files, the main_tex is the filename relative to temp_dir,
                    #     # and the main_folder is temp_dir itself.
                    # else:
                    #     raise FileNotFoundError(
                    #         f"Decompressed file {output_filename} from {compressed_path} is not a valid main TeX file."
                    #     )

                except gzip.BadGzipFile as gz_err:
                    # This specifically catches errors if it's a .gz file but not valid gzip format
                    raise IOError(
                        f"Could not process {compressed_path}. Invalid Gzip file format: {gz_err}"
                    ) from gz_err
                except (
                    Exception
                ) as e:  # Catch other potential errors during single file processing
                    raise IOError(
                        f"Error processing {compressed_path} as single gz file: {e}"
                    ) from e

            if not processed:
                raise ValueError(
                    f"Unsupported file type or error processing file: {compressed_path}"
                )

            # Yield the relative path of main_tex from temp_dir and temp_dir itself
            yield main_tex, temp_dir

        finally:
            # Clean up temporary directory
            if cleanup:
                shutil.rmtree(temp_dir)

    @classmethod
    def from_folder(cls, folder_path: str):
        """Create a TexReader instance from a folder containing TeX files.

        Args:
            folder_path (str): Path to the folder

        Returns:
            tuple: (main_tex_file, folder_path)
        """
        main_tex, main_folder = cls.find_main_tex_file(folder_path)
        return main_tex, main_folder

    @classmethod
    @contextmanager
    def from_compressed(
        cls, gz_path: str, temp_dir: Optional[str] = None, cleanup: bool = True
    ):
        """Create a TexReader instance from a compressed file.

        Args:
            gz_path (str): Path to the compressed file

        Yields:
            tuple: (main_tex_file, temp_dir)
                  main_tex_file: Name of the main TeX file
                  temp_dir: Path to temporary directory containing extracted files
        """
        with cls.process_compressed_file(
            gz_path, temp_dir=temp_dir, cleanup=cleanup
        ) as (
            main_tex,
            temp_dir,
        ):
            yield main_tex, temp_dir


if __name__ == "__main__":
    path = "./source.tar.gz"
    with TexFileExtractor.from_compressed(path, cleanup=False) as (
        main_tex,
        temp_dir,
    ):
        print("Found main tex %s in folder %s" % (main_tex, temp_dir))
