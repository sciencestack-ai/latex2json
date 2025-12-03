from latex2json.latex_maps.environments import (
    DOCUMENT_ENVIRONMENTS,
    MATH_ENVIRONMENTS,
    TABLE_ENVIRONMENTS,
    FIGURE_ENVIRONMENTS,
)
from latex2json.latex_maps.fonts import (
    LATEX_TO_FONT_STYLE,
    LEGACY_TO_FONT_STYLE,
)

# Commands that should NEVER be redefined (strict blocking)
STRICTLY_BLOCKED_COMMANDS = [
    # Core LaTeX primitives
    "noexpand",
    "expandafter",
    "newcommand",
    "def",
    "begin",
    "end",
    "newtheorem",
    # newlines
    "\\",
    "\\\\",
    # equation delimiters
    "(",  # \(
    ")",  # \)
    "[",  # \[
    "]",  # \]
    # Font commands - derived from fonts.py
    *LATEX_TO_FONT_STYLE.keys(),
    *LEGACY_TO_FONT_STYLE.keys(),
    # Additional font-related commands not in fonts.py
    "text",
    "mathversion",
]

# Commands that CAN be redefined but with wrapping to preserve semantics
PROTECTED_COMMANDS = [
    # Sections
    "section",
    "subsection",
    "subsubsection",
    "paragraph",
    "subparagraph",
    "part",
    "chapter",
    # Document structure
    "abstract",
    "bibliography",
    "appendix",
    "appendices",
    # References and citations
    "cite",
    "citep",
    "citet",
    "bibitem",
    "url",
    "ref",
    # Floats
    "table",
    "figure",
    "caption",
    "captionof",
    # Misc
    "date",
    "and",
    "newline",
    # Bib commands
    "bysame",
]

WHITELISTED_ENVIRONMENTS = []
for env in (
    list(DOCUMENT_ENVIRONMENTS.keys())
    + list(TABLE_ENVIRONMENTS.keys())
    + list(FIGURE_ENVIRONMENTS.keys())
):
    WHITELISTED_ENVIRONMENTS.append(env)

for env, env_def in MATH_ENVIRONMENTS.items():
    WHITELISTED_ENVIRONMENTS.append(env)
    if env_def.begin_command:
        # e.g. prevent \equation and \endequation from being overridden
        STRICTLY_BLOCKED_COMMANDS.append(env_def.begin_command)
    if env_def.end_command:
        STRICTLY_BLOCKED_COMMANDS.append(env_def.end_command)


WHITELISTED_PACKAGES = ["subfiles", "fancyhdr", "natbib", "algorithmic", "IEEEtran"]
WHITELISTED_CLASSES = WHITELISTED_PACKAGES.copy()
