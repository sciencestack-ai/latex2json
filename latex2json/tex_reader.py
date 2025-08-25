import logging
import os
import json
from typing import Dict, List, TypeVar, Callable, Any, Tuple, Optional
import warnings
from dataclasses import dataclass
from pathlib import Path
import shutil

from latex2json.tex_file_extractor import TexFileExtractor
from latex2json.renderer.json import JSONRenderer

T = TypeVar("T")

BaseToken = Dict[str, Any]


@dataclass
class ProcessingResult:
    """Represents the result of processing a TeX file."""

    tokens: List[BaseToken]
    color_map: Optional[Dict[str, Dict[str, str]]] = None

    main_tex_path: Optional[Path] = None
    temp_dir: Optional[Path] = None

    def cleanup(self):
        """Clean up temporary resources."""
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None


def merge_inline_tokens_func(tokens: List[Dict]) -> List[Dict]:
    """
    Merge consecutive inline tokens into a single text token recursively.

    Args:
        tokens: List of token dictionaries

    Returns:
        List of merged tokens
    """
    MERGE_TYPES = ["text", "ref", "citation"]
    merged: List[Dict] = []
    buffer = ""

    def is_merge_candidate(token: Dict) -> bool:
        """Check if token is candidate for merging."""
        # First check if token is a dict
        if not isinstance(token, dict):
            return False
        return token["type"] in MERGE_TYPES or (
            token["type"] == "equation" and token.get("display") != "block"
        )

    def get_candidate_value(token: Dict) -> str:
        """Get string value for merging."""
        if not isinstance(token, dict):
            return str(token)
        if token["type"] == "text":
            return token["content"]
        elif token["type"] == "equation" and token.get("display") != "block":
            return f"${token['content']}$"
        elif token["type"] == "ref":
            content_str = ",".join(token["content"])
            return f"\\ref{{{content_str}}}"
        elif token["type"] == "citation":
            content_str = ",".join(token["content"])
            return f"\\cite{{{content_str}}}"
        return str(token.get("content", ""))

    def process_token(token: Dict) -> Dict:
        """Process a token and its nested content recursively."""
        if not token or not isinstance(token, dict):
            return token

        # Handle nested content
        if "content" in token and isinstance(token["content"], list):
            token["content"] = merge_inline_tokens_func(token["content"])
        return token

    for token in tokens:
        if token and is_merge_candidate(token):
            buffer += get_candidate_value(process_token(token))
        else:
            if buffer:
                merged.append({"type": "text", "content": buffer})
                buffer = ""
            merged.append(process_token(token))

    if buffer:
        merged.append({"type": "text", "content": buffer})

    return merged


class TexProcessingError(Exception):
    """Base exception for TeX processing errors."""

    pass


class TexReader:
    """
    Handles reading and processing TeX files into tokens and JSON output.

    Attributes:
        logger: Logger instance for tracking operations
    """

    def __init__(self, logger: Optional[logging.Logger] = None, n_processors: int = 1):
        self.logger = logger or logging.getLogger(__name__)
        self.json_renderer = JSONRenderer(logger=self.logger, n_processors=n_processors)

    def clear(self):
        self.json_renderer.clear()

    def _handle_file_operation(
        self, operation: Callable[..., T], error_msg: str, *args, **kwargs
    ) -> T:
        """
        Generic error handler for file operations.

        Args:
            operation: Callable to execute
            error_msg: Error message template
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation

        Returns:
            Result of the operation

        Raises:
            FileNotFoundError: If required files are missing
            TexProcessingError: If processing fails
        """
        try:
            return operation(*args, **kwargs)
        except FileNotFoundError as e:
            self.logger.error("File not found error: %s", str(e), exc_info=True)
            raise
        except Exception as e:
            self.logger.error("%s: %s", error_msg, str(e), exc_info=True)
            raise TexProcessingError(f"{error_msg}: {str(e)}") from e

    def _verify_file_exists(self, file_path: Path, file_type: str = "File") -> None:
        """
        Verify file exists and log appropriate error if not.

        Args:
            file_path: Path to verify
            file_type: Type of file for error messaging

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"{file_type} not found: {file_path}")

    def process_file(self, file_path: Path | str) -> ProcessingResult:
        """
        Process a single TeX file and return the token output.

        Args:
            file_path: Path to the TeX file

        Returns:
            ProcessingResult containing the processed tokens

        Raises:
            FileNotFoundError: If file doesn't exist
            TexProcessingError: If processing fails
        """
        file_path = Path(file_path)

        def _process() -> ProcessingResult:
            self.clear()
            self._verify_file_exists(file_path)
            output = self.json_renderer.parse_file(file_path) or []
            # tokens = self.parser.parse_file(file_path)
            # output = self.token_builder.build(tokens)
            color_map = self.json_renderer.get_colors()
            # self.clear()
            return ProcessingResult(
                tokens=output,
                color_map=color_map,
                main_tex_path=file_path,
            )

        return self._handle_file_operation(
            _process, f"Failed to process TeX file {file_path}"
        )

    def to_json(self, result: ProcessingResult, merge_inline_tokens=False) -> str:
        """
        Convert token output to JSON string.

        Args:
            result: ProcessingResult containing tokens to convert

        Returns:
            JSON string representation of the tokens

        Raises:
            TexProcessingError: If conversion fails
        """

        def _convert() -> str:
            # with warnings.catch_warnings():
            #     warnings.filterwarnings("ignore", module="pydantic")
            #     json_output = [
            #         t.model_dump(mode="json", exclude_none=True) for t in result.tokens
            #     ]
            data = {
                "tokens": result.tokens,
                "color_map": result.color_map,
            }
            if merge_inline_tokens:
                data["tokens"] = merge_inline_tokens_func(data["tokens"])
            # ensure_ascii=False to prevent unnecessary escape characters
            return json.dumps(data, ensure_ascii=False)

        return self._handle_file_operation(_convert, "Failed to convert tokens to JSON")

    def save_to_json(
        self, result: ProcessingResult, json_path: Path | str = "output.json"
    ) -> None:
        """
        Save token output to JSON file.

        Args:
            result: ProcessingResult containing tokens to save
            json_path: Path where to save the JSON

        Raises:
            TexProcessingError: If saving fails
        """
        json_path = Path(json_path)

        def _save() -> None:
            json_output = self.to_json(result)
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(json_output, encoding="utf-8")
            self.logger.info("Successfully saved output to %s", json_path)

        return self._handle_file_operation(
            _save, f"Failed to save JSON output to {json_path}"
        )

    def process_compressed(
        self, compressed_path: str, temp_dir: Optional[str] = None, cleanup: bool = True
    ):
        """Process a compressed TeX file and save results to JSON."""
        if not os.path.exists(compressed_path):
            error_msg = f"Compressed file not found: {compressed_path}"
            self.logger.error(error_msg, exc_info=True)
            raise FileNotFoundError(error_msg)

        try:
            with TexFileExtractor.from_compressed(
                compressed_path, temp_dir=temp_dir, cleanup=cleanup
            ) as (
                main_tex,
                temp_dir,
            ):
                self.logger.info(
                    f"Found main TeX file in archive: {main_tex}, {compressed_path}"
                )
                file_path = os.path.join(temp_dir, main_tex)
                output = self.process_file(file_path)
                output.temp_dir = temp_dir
                return output
        except Exception as e:
            error_msg = f"Failed to process compressed file {compressed_path}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

    def process_folder(self, folder_path: str | Path) -> ProcessingResult:
        """Process a folder containing TeX files and return results.

        Args:
            folder_path: Path to the folder containing TeX files

        Returns:
            ProcessingResult containing the processed tokens

        Raises:
            FileNotFoundError: If folder doesn't exist or no main TeX file found
            TexProcessingError: If processing fails
        """
        folder_path = Path(folder_path)

        def _process() -> ProcessingResult:
            self._verify_file_exists(folder_path, file_type="Folder")
            main_tex, _ = TexFileExtractor.from_folder(str(folder_path))
            self.logger.info(
                f"Found main TeX file in folder: {main_tex}, {folder_path}"
            )
            file_path = folder_path / main_tex
            return self.process_file(file_path)

        return self._handle_file_operation(
            _process, f"Failed to process TeX folder {folder_path}"
        )

    def process(
        self, input_path: str | Path, cleanup: bool = False
    ) -> ProcessingResult:
        """
        Process input which can be a single file, folder, or compressed archive.

        Args:
            input_path: Path to the input (file, folder, or compressed archive)
            cleanup: Whether to clean up temporary files (for compressed archives)

        Returns:
            ProcessingResult containing the processed tokens

        Raises:
            FileNotFoundError: If input doesn't exist
            TexProcessingError: If processing fails
        """
        input_path = Path(input_path)
        self._verify_file_exists(input_path)

        def _process() -> ProcessingResult:
            if input_path.is_dir():
                return self.process_folder(input_path)
            elif input_path.suffix in [".gz", ".tar.gz", ".tgz", ".zip"]:
                result = self.process_compressed(str(input_path), cleanup=False)
                if cleanup:
                    result.cleanup()
                return result
            else:
                return self.process_file(input_path)

        return self._handle_file_operation(
            _process, f"Failed to process input {input_path}"
        )


if __name__ == "__main__":
    from latex2json.utils.logger import setup_logger

    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logger = setup_logger(level=logging.DEBUG, log_file="logs/tex_reader.log")

    tex_reader = TexReader(logger, n_processors=1)

    # # Example usage with compressed file
    # gz_file = "papers/arXiv-2301.10945v1.tar.gz"
    # output, temp_dir = tex_reader.process_compressed(gz_file)
    # tex_reader.save_to_json(output)

    # Example usage with folder
    target_folder = "outputs"
    folders = [
        # "papers/new/arXiv-math0503066v2",
        # "papers/tested/arXiv-1509.05363v6",
        # "papers/tested/arXiv-1706.03762v7",
        # "papers/tested/arXiv-2303.08774v6",
        # "papers/tested/arXiv-2301.10945v1",
        # "papers/tested/arXiv-1907.11692v1",
        # "papers/tested/arXiv-1712.01815v1",
        # "papers/new/arXiv-2304.02643v1",
        # "papers/tested/arXiv-2010.13219v3",
        # "papers/tested/arXiv-1710.09829v2",
        # "papers/tested/arXiv-1512.03385v1",
        # # "papers/new/arXiv-hep-th0603057v3",
        # "papers/tested/arXiv-math9404236v1.tex",
        # # "papers/tested/arXiv-2301.10303v4.tex",
        # "papers/tested/arXiv-2105.02865v3.tex",
        # "papers/arXiv-2301.10945v1.tar.gz",
        # "papers/tested/arXiv-1509.05363v6"
        # "papers/tested/arXiv-2301.10945v1"
        # "papers/tested/arXiv-2408.07934v1"
        # "papers/tested/arXiv-1712.01815v1"
        "papers/new/arXiv-2103.07867v1.gz",
        # "/Users/cj/Downloads/arXiv-math0610903v1.gz"
        # "papers/new/arXiv-0911.5501v2"
    ]
    merge_inline = False
    stem_postfix = "_merged" if merge_inline else ""

    cleanup = True

    for folder in folders:
        folder_stem = folder.split("/")[-1]
        save_path = target_folder + "/" + folder_stem + stem_postfix + ".json"
        # output = tex_reader.process_compressed(
        #     folder, temp_dir="papers/new/arXiv-2103.07867v1", cleanup=cleanup
        # )
        output = tex_reader.process(folder)
        try:
            json_output = tex_reader.to_json(output, merge_inline_tokens=merge_inline)
            # tex_reader.save_to_json(output, save_path)
            with open(save_path, "w") as f:
                f.write(json_output)
            print("SAVED TO", save_path)
        finally:
            if cleanup:
                output.cleanup()  # Ensure cleanup happens even if save_to_json fails
