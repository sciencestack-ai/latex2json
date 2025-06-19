from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.types import Token

formatting_patterns = {
    "NeedsTeXFormat": 1,
    "ProvidesClass": "{[",
    "ProvidesPackage": "{[",
    # tcb
    "tcbset": "{",
    "tcbuselibrary": "{",
    # Float-related formatting
    "floatstyle": 1,
    "restylefloat": 1,
    # Section-related formatting
    "titleformat": 4,
    "titlespacing": 4,
    "sectionformat": 1,
    # Font-related formatting
    "setmathfont": "[{",
    "setmainfont": 1,
    "setsansfont": 1,
    "setmonofont": 1,
    "fontsize": 2,
    "selectfont": 0,
    "usefont": 4,
    # You might also add:
    "geometry": 1,  # \geometry{margin=1in}
    "setstretch": 1,  # \setstretch{1.5} - line spacing
    # Package processing
    "ProcessOptions": 0,  # Actually takes no arguments
    "PassOptionsToClass": 2,
    "PassOptionsToPackage": 2,
    "ExecuteBibliographyOptions": 1,
    # pdf options
    "pdfinfo": "{",
    "pdfoutput": "=i",
    "pdfsuppresswarningpagegroup": "=i",
    # Page-related formatting
    "pagestyle": 1,
    "newpagestyle": 2,
    "renewpagestyle": 2,
    "thispagestyle": 1,
    "enlargethispage": 1,
    "pagecolor": "*{",
    "centering": 0,
    "raggedright": 0,
    "raggedleft": 0,
    "allowdisplaybreaks": 0,
    "samepage": 0,
    "thepage": 0,
    "indent": 0,
    "noindent": 0,
    "par": 0,
    "clearpage": 0,
    "cleardoublepage": 0,
    "nopagebreak": 0,
    "hss": 0,
    "hfill": 0,
    "hfil": 0,
    "vfill": 0,
    "vfil": 0,
    "sloppy": 0,
    "flushbottom": 0,
    "flushleft": 0,
    "flushright": 0,
    "flushtop": 0,
    # Style commands
    "urlstyle": 1,
    "theoremstyle": 1,
    "bibliographystyle": 1,
    "documentstyle": 1,
    "setcitestyle": 1,
    # lists and items
    "lstset": "{",
    "setlist": "[{",
    # Width-related commands
    "linewidth": 0,
    "columnwidth": 0,
    "textwidth": 0,
    "hsize": 0,
    "labelwidth": 0,
    "width": 0,
    # toolset
    "mathtoolsset": "[",
    # penalty
    "penalty": "=f",
    "clubpenalty": "=f",
    "widowpenalty": "=f",
    "discretionarypenalty": "=f",
    "interfootnotelinepenalty": "=f",
    # \kern, which is technically spacing but more like a length between characters. so ignore
    "kern": "d",
    # setup
    "hypersetup": "[{",
    "captionsetup": "[{",
    #
    "tracinglostchars": "=i",
    # language
    "setdefaultlanguage": 1,
    # class
    "subjclass": "[{",
    # mathstack
    "stackMath": 0,
    # physics
    "pacs": 1,
    # other
    "pz@": 0,
    "phantomsection": 0,
    "FloatBarrier": 0,
    "footins": 0,
    "/": 0,  # \/ (in latex, this is like an empty space)
    # newwmdev
    "newmdenv": "[{",
}

content_formatting_patterns = {
    # title
    "maketitle": 0,
    "@title": 0,
    "titlecontents": "{[{{{{[",
    # TOCs
    "tableofcontents": 0,
    # other contents
    "addtocontents": "{{",
    "addcontentsline": "{{{",
    "contentspage": 0,
    "startcontents": 0,
    "printcontents": 3,
    "hyphenation": 1,
    # page numbers
    "pagenumbering": 1,
    # line numbers
    "linenumbers": 0,
    "linesnumbered": 0,
    # bib
    "printbibliography": 0,
    "renewbibmacro": "{{",
    # datetime
    "date": "{",
    "today": 0,
    # counter
    "AddEnumerateCounter": 3,
}


def two_column_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    out_tokens = expander.parse_bracket_as_tokens(expand=True)
    return out_tokens


def texorpdfstring_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    blocks = expander.parse_braced_blocks(2, expand=True)
    if len(blocks) != 2:
        expander.logger.warning("Expected 2 blocks for \\texorpdfstring")
        return []
    # choose the second block
    return blocks[1]


def register_ignore_format_handlers(expander: ExpanderCore):
    """Register all formatting-related command handlers"""
    register_ignore_handlers_util(expander, formatting_patterns)
    register_ignore_handlers_util(expander, content_formatting_patterns)

    # columns
    register_ignore_handlers_util(expander, {"onecolumn": 0})
    expander.register_handler("twocolumn", two_column_handler)
    # texorpdfstring
    expander.register_handler("texorpdfstring", texorpdfstring_handler)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_ignore_format_handlers(expander)

    # Test some formatting commands
    out1 = expander.expand(r"\floatname{figure}{Fig.}")
    out2 = expander.expand(r"\pagestyle{fancy}")
    out3 = expander.expand(
        r"\titleformat{\section}{\normalfont\Large\bfseries}{\thesection}{1em}{}"
    )
