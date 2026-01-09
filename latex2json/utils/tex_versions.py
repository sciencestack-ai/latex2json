from pathlib import Path
import re
from typing import List, Tuple

from latex2json.utils.encoding import read_file
from latex2json.utils.tex_utils import strip_latex_comments


# Pre-compiled patterns for AMSTeX detection (threshold=3 to trigger)
_AMSTEX_PATTERNS: List[Tuple[re.Pattern, int]] = [
    (re.compile(r"\\input\s+amstex", re.IGNORECASE), 3),  # Strong indicator
    (re.compile(r"\\documentstyle.*ams\w+", re.IGNORECASE), 2),
    (re.compile(r"\\topmatter", re.IGNORECASE), 2),
    (re.compile(r"\\heading.*?\\endheading", re.DOTALL), 2),
    (re.compile(r"\\magnification\s*=", re.IGNORECASE), 1),
    (re.compile(r"\\define\s+\\[a-zA-Z]+", re.IGNORECASE), 1),
    (re.compile(r"\\proclaim\s", re.IGNORECASE), 1),
    (re.compile(r"\\demo\s", re.IGNORECASE), 1),
    (re.compile(r"\\roster\s", re.IGNORECASE), 1),
]

# Pre-compiled patterns for expl3 detection (threshold=3 to trigger)
_EXPL3_PATTERNS: List[Tuple[re.Pattern, int]] = [
    (re.compile(r"\\ProvidesExplPackage"), 3),
    (re.compile(r"\\ProvidesExplClass"), 3),
    (re.compile(r"\\ExplSyntaxOn"), 3),
    (re.compile(r"\\ExplSyntaxOff"), 3),
    (re.compile(r"\\RequirePackage\s*\{\s*expl3\s*\}"), 3),
]


def _check_content_matches_pattern(
    content: str, weighted_patterns: List[Tuple[re.Pattern, int]], threshold: int = 3
) -> bool:
    cnt = 0
    for pattern, weight in weighted_patterns:
        if pattern.search(content):
            cnt += weight
            if cnt >= threshold:
                return True
    return False


def is_content_amstex(content: str) -> bool:
    """
    Detect if content uses AMSTeX format instead of LaTeX.
    AMSTeX is largely obsolete but may still appear in legacy documents.
    """
    return _check_content_matches_pattern(content, _AMSTEX_PATTERNS)


def is_content_expl3(content: str) -> bool:
    """
    Detect if content uses LaTeX3/expl3 programming layer syntax.
    ExplSyntax uses special naming conventions and catcode changes.
    """
    return _check_content_matches_pattern(content, _EXPL3_PATTERNS)


def is_supported_tex_version(file_path: Path | str) -> Tuple[bool, str]:
    content = read_file(str(file_path))
    content = strip_latex_comments(content)
    # AMSTeX is now supported via preprocessing (see amstex_expander.py)
    if is_content_expl3(content):
        return False, "Expl3 not supported"
    return True, ""
