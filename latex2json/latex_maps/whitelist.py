from latex2json.latex_maps.environments import (
    DOCUMENT_ENVIRONMENTS,
    MATH_ENVIRONMENTS,
    TABLE_ENVIRONMENTS,
    FIGURE_ENVIRONMENTS,
)

MAKETITLE_COMMANDS = [
    # only disable redefinition of @maketitle to ignore layout and preserve metadata
    "@maketitle",
    # allow redefinition of maketitle and author, title, thanks
    # "maketitle",
    # "@author",
    # "author",
    # "@title",
    # "title",
    # "@thanks",
    # "thanks",
]

# These commands should not be overrwritten by newcommand/newenvironment
WHITELISTED_COMMANDS = [
    *MAKETITLE_COMMANDS,
    # expand
    "noexpand",
    "expandafter",
    # sections
    "bibliography",
    "newcommand",
    "def",
    "begin",
    "end",
    "section",
    "subsection",
    "subsubsection",
    "paragraph",
    "subparagraph",
    "newline",
    "newtheorem",
    "date",
    "and",
    "part",
    "chapter",
    "abstract",
    "table",
    "figure",
    "cite",
    "citep",
    "citet",
    "caption",
    "captionof",
    "bibitem",
    "url",
    "ref",
    "appendix",
    "appendices",
    "\\",
    "\\\\",
    # text font
    "textbf",
    "textit",
    "textsl",
    "textsc",
    "textsf",
    "texttt",
    "textrm",
    "textup",
    "emph",
    # text size
    "texttiny",
    "textscriptsize",
    "textfootnotesize",
    "textsmall",
    "textnormal",
    "textlarge",
    "texthuge",
    "text",
    # legacy font
    # Basic text style commands
    "tt",
    "bf",
    "it",
    "sl",
    "sc",
    "sf",
    "rm",
    "em",
    "bold",
    # Font family declarations
    "rmfamily",
    "sffamily",
    "ttfamily",
    # Font shape declarations
    "itshape",
    "scshape",
    "upshape",
    "slshape",
    # Font series declarations
    "bfseries",
    "mdseries",
    # Font combinations and resets
    "normalfont",
    # Additional text mode variants
    "textup",
    "textnormal",
    "textmd",
    # math stuff (often used directly before math mode)
    "unboldmath",
    "boldmath",
    "mathversion",
    # Basic size commands
    "tiny",
    "scriptsize",
    "footnotesize",
    "small",
    "normalsize",
    "large",
    "Large",
    "LARGE",
    "huge",
    "Huge",
    # Additional size declarations
    "smaller",
    "larger",
    # bib stuff
    "bysame",
]


WHITELISTED_ENVIRONMENTS = []
for env in (
    list(DOCUMENT_ENVIRONMENTS.keys())
    + list(MATH_ENVIRONMENTS.keys())
    + list(TABLE_ENVIRONMENTS.keys())
    + list(FIGURE_ENVIRONMENTS.keys())
):
    WHITELISTED_ENVIRONMENTS.append(env)
    WHITELISTED_ENVIRONMENTS.append(env + "*")


WHITELISTED_PACKAGES = ["subfiles", "fancyhdr", "natbib", "algorithmic"]
WHITELISTED_CLASSES = WHITELISTED_PACKAGES.copy()
