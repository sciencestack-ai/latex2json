from pathlib import Path
import re
from typing import Dict, List, Tuple

from latex2json.utils.encoding import read_file
from latex2json.utils.tex_utils import strip_latex_comments


def _check_content_matches_pattern(
    content: str, weighted_patterns: List[Tuple[re.Pattern, int]], threshold: int = 1
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
    amstex_patterns = [
        (
            re.compile(r"\\input\s+amstex", re.IGNORECASE),
            3,
        ),  # Direct amstex input is strong indicator
        (
            re.compile(r"\\documentstyle.*ams\w+", re.IGNORECASE),
            2,
        ),  # AMS document style suggests amstex
        (re.compile(r"\\topmatter", re.IGNORECASE), 2),  # Common amstex command
        (
            re.compile(r"\\heading.*?\\endheading", re.DOTALL),
            2,
        ),  # Amstex heading syntax
        (
            re.compile(r"\\magnification\s*=", re.IGNORECASE),
            1,
        ),  # Used in amstex but could be elsewhere
        (
            re.compile(r"\\define\s+\\[a-zA-Z]+", re.IGNORECASE),
            1,
        ),  # Macro definition style
        (re.compile(r"\\proclaim\s", re.IGNORECASE), 1),
        (re.compile(r"\\demo\s", re.IGNORECASE), 1),
        (re.compile(r"\\roster\s", re.IGNORECASE), 1),
    ]

    return _check_content_matches_pattern(content, amstex_patterns, threshold=3)


def is_content_expl3(content: str) -> bool:
    """
    Detect if content uses LaTeX3/expl3 programming layer syntax.
    ExplSyntax uses special naming conventions and catcode changes.
    """
    expl3_patterns = [
        (re.compile(r"\\ProvidesExplPackage"), 3),  # Direct expl3 package declaration
        (re.compile(r"\\ProvidesExplClass"), 3),  # Direct expl3 class declaration
        (re.compile(r"\\ExplSyntaxOn"), 3),  # Explicit expl3 syntax marker
        (re.compile(r"\\ExplSyntaxOff"), 3),  # Explicit expl3 syntax marker
        (
            re.compile(r"\\RequirePackage\s*\{\s*expl3\s*\}"),
            3,
        ),  # Direct expl3 requirement
        # (re.compile(r"\\c_[a-zA-Z_]+"), 1),  # Constant variable pattern
        # (re.compile(r"\\g_[a-zA-Z_]+"), 1),  # Global variable pattern
        # (re.compile(r"\\l_[a-zA-Z_]+"), 1),  # Local variable pattern
        # (re.compile(r"\\tl_[a-zA-Z_]+"), 1),  # Token list functions
        # (re.compile(r"\\seq_[a-zA-Z_]+"), 1),  # Sequence functions
        # (re.compile(r"\\int_[a-zA-Z_]+"), 1),  # Integer functions
        # (re.compile(r"\\bool_[a-zA-Z_]+"), 1),  # Boolean functions
    ]

    return _check_content_matches_pattern(content, expl3_patterns, threshold=3)


def is_supported_tex_version(file_path: Path | str) -> Tuple[bool, str]:
    content = read_file(str(file_path))
    content = strip_latex_comments(content)
    if is_content_amstex(content):
        return False, "AMSTeX not supported"
    if is_content_expl3(content):
        return False, "Expl3 not supported"
    return True, ""
