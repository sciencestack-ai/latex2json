from pathlib import Path
import re
from typing import Dict, List, Tuple

from latex2json.utils.encoding import read_file
from latex2json.utils.tex_utils import strip_latex_comments


def _check_content_matches_pattern(
    content: str, weighted_patterns: Dict[str, int], threshold: int = 1
) -> bool:
    cnt = 0
    for pattern, weight in weighted_patterns.items():
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            cnt += weight
            if cnt >= threshold:
                return True
    return False


def is_content_amstex(content: str) -> bool:
    """
    Detect if content uses AMSTeX format instead of LaTeX.
    AMSTeX is largely obsolete but may still appear in legacy documents.
    """
    amstex_patterns = {
        r"\\input\s+amstex": 3,  # Direct amstex input is strong indicator
        r"\\documentstyle.*ams\w+": 2,  # AMS document style suggests amstex
        r"\\topmatter": 2,  # Common amstex command
        r"\\heading.*?\\endheading": 2,  # Amstex heading syntax
        r"\\magnification\s*=": 1,  # Used in amstex but could be elsewhere
        r"\\define\s+\\[a-zA-Z]+": 1,  # Macro definition style
        r"\\proclaim\s": 1,  # Amstex environment
        r"\\demo\s": 1,  # Amstex environment
        r"\\roster\s": 1,  # Amstex environment
    }

    return _check_content_matches_pattern(content, amstex_patterns, threshold=3)


def is_content_expl3(content: str) -> bool:
    """
    Detect if content uses LaTeX3/expl3 programming layer syntax.
    ExplSyntax uses special naming conventions and catcode changes.
    """
    expl3_patterns = {
        r"\\ProvidesExplPackage": 3,  # Direct expl3 package declaration
        r"\\ProvidesExplClass": 3,  # Direct expl3 class declaration
        r"\\ExplSyntaxOn": 3,  # Explicit expl3 syntax marker
        r"\\ExplSyntaxOff": 3,  # Explicit expl3 syntax marker
        r"\\RequirePackage\s*\{\s*expl3\s*\}": 3,  # Direct expl3 requirement
        r"\\[a-zA-Z]+_[a-zA-Z_]*:[a-zA-Z]*": 2,  # Function naming pattern
        r"\\__[a-zA-Z]+_[a-zA-Z_]*:[a-zA-Z]*": 2,  # Internal function pattern
        r"\\c_[a-zA-Z_]+": 1,  # Constant variable pattern
        r"\\g_[a-zA-Z_]+": 1,  # Global variable pattern
        r"\\l_[a-zA-Z_]+": 1,  # Local variable pattern
        r"\\tl_[a-zA-Z_]+": 1,  # Token list functions
        r"\\seq_[a-zA-Z_]+": 1,  # Sequence functions
        r"\\int_[a-zA-Z_]+": 1,  # Integer functions
        r"\\bool_[a-zA-Z_]+": 1,  # Boolean functions
    }

    return _check_content_matches_pattern(content, expl3_patterns, threshold=3)


def is_supported_tex_version(file_path: Path | str) -> Tuple[bool, str]:
    content = read_file(str(file_path))
    content = strip_latex_comments(content)
    if is_content_amstex(content):
        return False, "AMSTeX not supported"
    if is_content_expl3(content):
        return False, "Expl3 not supported"
    return True, ""
