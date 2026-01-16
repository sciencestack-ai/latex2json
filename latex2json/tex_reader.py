import logging
import os
import json
from typing import Dict, List, TypeVar, Callable, Any, Tuple, Optional
import warnings
from dataclasses import dataclass
from pathlib import Path
import shutil

from latex2json.expander.expander import Expander
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
    project_root: Optional[Path] = None
    temp_dir: Optional[Path] = None

    def cleanup(self):
        """Clean up temporary resources."""
        if self.temp_dir:
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None


class TexProcessingError(Exception):
    """Base exception for TeX processing errors."""

    pass


class TexReader:
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        n_processors: int = 1,
        ignore_package_cls: bool = False,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self._ignore_package_cls = ignore_package_cls

        # Create expander with initial settings
        expander = Expander(logger=self.logger, ignore_package_cls=ignore_package_cls)

        # Pass expander to renderer
        self.json_renderer = JSONRenderer(
            logger=self.logger,
            n_processors=n_processors,
            expander=expander,
        )

    def clear(self):
        # Create fresh expander with current settings
        new_expander = Expander(
            logger=self.logger, ignore_package_cls=self._ignore_package_cls
        )
        self.json_renderer.clear(expander=new_expander)

    @property
    def ignore_package_cls(self) -> bool:
        return self._ignore_package_cls

    @ignore_package_cls.setter
    def ignore_package_cls(self, value: bool):
        self._ignore_package_cls = value
        self.json_renderer.expander.ignore_package_cls = value

    def _handle_file_operation(
        self, operation: Callable[..., T], error_msg: str, *args, **kwargs
    ) -> T:
        try:
            return operation(*args, **kwargs)
        except FileNotFoundError as e:
            self.logger.error("File not found error: %s", str(e), exc_info=True)
            raise
        except Exception as e:
            self.logger.error("%s: %s", error_msg, str(e), exc_info=True)
            raise TexProcessingError(f"{error_msg}: {str(e)}") from e

    def _verify_file_exists(self, file_path: Path, file_type: str = "File") -> None:
        if not file_path.exists():
            raise FileNotFoundError(f"{file_type} not found: {file_path}")

    def process_file(
        self, file_path: Path | str, project_root: Path | str = None
    ) -> ProcessingResult:
        file_path = Path(file_path)
        if project_root:
            project_root = Path(project_root)
        else:
            # Default to parent directory of the file
            project_root = file_path.parent

        self.clear()
        self._verify_file_exists(file_path)
        # is_supported, error_msg = is_supported_tex_version(file_path)
        # if not is_supported:
        #     raise TexProcessingError(f"Unsupported TeX version: {error_msg}")
        output = (
            self.json_renderer.parse_file(
                file_path, project_root=str(project_root) if project_root else None
            )
            or []
        )
        color_map = self.json_renderer.get_colors()

        return ProcessingResult(
            tokens=output,
            color_map=color_map,
            main_tex_path=file_path,
            project_root=project_root,
        )

    def to_json(self, result: ProcessingResult) -> str:
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
            # ensure_ascii=False to prevent unnecessary escape characters
            return json.dumps(data, ensure_ascii=False)

        return self._handle_file_operation(_convert, "Failed to convert tokens to JSON")

    def save_to_json(
        self, result: ProcessingResult, json_path: Path | str = "output.json"
    ) -> None:
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
        if not os.path.exists(compressed_path):
            raise FileNotFoundError(f"Compressed file not found: {compressed_path}")

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
            output = self.process_file(file_path, project_root=temp_dir)
            output.temp_dir = Path(temp_dir)
            return output

    def process_folder(self, folder_path: str | Path) -> ProcessingResult:
        folder_path = Path(folder_path)

        self._verify_file_exists(folder_path, file_type="Folder")
        main_tex, _ = TexFileExtractor.from_folder(str(folder_path))
        self.logger.info(f"Found main TeX file in folder: {main_tex}, {folder_path}")
        file_path = folder_path / main_tex
        return self.process_file(file_path, project_root=folder_path)

    def process(
        self, input_path: str | Path, cleanup: bool = False
    ) -> ProcessingResult:
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
        # "papers/new/arXiv-2103.07867v1.gz",
        # "papers/new/euler-nordstroem"
        # "papers/tested/arXiv-2301.10945v1"
        # TODO
        # "papers/faulty/math_0503351v1",
        # "papers/faulty/math_0504203v3",
        # "/Users/cj/Downloads/new.tex",
        # "papers/tested/arXiv-1703.06870v3"
        # "papers/tested/arXiv-1509.05363v6"
        # "papers/new/arXiv-2410.23255v2"
        # "papers/new/arXiv-2509.20328v1"
        # "papers/faulty/math_0501127v1"
        # "papers/new/arXiv-2510.00179v1"
        # "papers/faulty/math_0504455v1"
        # "/Users/cj/Documents/python/latex_pipeline/tests/test_data"
        # "/Users/cj/Documents/python/latex2json/tests/samples/diagram_sourcefiles"
        # "papers/tested/arXiv-1509.05363v6"
        # "papers/tested/arXiv-2010.11929v2"
        # "papers/tested/arXiv-2103.13713v1"
        # "papers/new/arXiv-2401.10020v3"
        # "papers/new/arXiv-2408.15154v1"
        # "papers/new/arXiv-2510.26692v2"
        # "/Users/cj/Downloads/WTF_1106.1813v1.SMOTE__Synthetic_Minority_Over_sampling_Technique.tar.gz"
        # "/Users/cj/Downloads/einstein-euler-local"
        # "papers/new/arXiv-2511.11092v1"
        # "papers/new/arXiv-2511.07416v1"
        # "/Users/cj/Downloads/arXiv-2105.10386v1"
        # "/Users/cj/Documents/science_ai/test_tex/project_test/test_paper.tex"
        # "/Users/cj/Downloads/arXiv-1612.09375v2"
        # "/Users/cj/Downloads/arXiv-2512.01948v1"
        # "/Users/cj/Downloads/arXiv-2511.17959v1"
        # TODO
        "/Users/cj/Downloads/arXiv-2510.17581v1"
        # "/Users/cj/Downloads/arXiv-2512.23707v1"
        # "/Users/cj/Downloads/arXiv-2407.06968v6"
        # "/Users/cj/Downloads/arXiv-2506.21373v2"
        # "/Users/cj/Downloads/arXiv-2512.16649v1"
        # "/Users/cj/Downloads/arXiv-1706.07269v3"
        # "/Users/cj/Downloads/arXiv-2503.20783v2",
        # "/Users/cj/Downloads/arXiv-2209.03003v1",
        # "/Users/cj/Downloads/arXiv-2301.04104v2",
        # "/Users/cj/Downloads/arXiv-2512.03130v1",
    ]
    cleanup = True

    # tex_reader.ignore_package_cls = True

    for folder in folders:
        folder_stem = folder.split("/")[-1]
        if os.path.isdir(folder):
            save_path = folder + "/latex2json.json"
        else:
            save_path = os.path.splitext(folder)[0] + ".json"
        # output = tex_reader.process_compressed(
        #     folder, temp_dir="papers/new/arXiv-2103.07867v1", cleanup=cleanup
        # )
        output = tex_reader.process(folder)
        try:
            json_output = tex_reader.to_json(output)
            # tex_reader.save_to_json(output, save_path)
            with open(save_path, "w") as f:
                json.dump(json.loads(json_output), f, indent=2, ensure_ascii=False)
            print("SAVED TO", save_path)
        finally:
            if cleanup:
                output.cleanup()  # Ensure cleanup happens even if save_to_json fails
