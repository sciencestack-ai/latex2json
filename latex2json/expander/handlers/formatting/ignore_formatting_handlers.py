from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.types import Token, TokenType

formatting_patterns = {
    "NeedsTeXFormat": 1,
    "ProvidesClass": "{[",
    "ProvidesPackage": "{[",
    # Float-related formatting
    "floatstyle": 1,
    "restylefloat": 1,
    # Section-related formatting
    "titleformat": "*{[" + "{" * 4,
    "titlespacing": "*" + "{" * 4,
    "titlelabel": "{",
    "titleclass": "{{[",
    "titlecontents": "{[" + "{" * 4,
    "titleline": "{",
    "sectionformat": 1,
    # Font-related formatting
    "setmathfont": "[{",
    "theorembodyfont": "{",
    "setmainfont": 1,
    "setsansfont": 1,
    "setmonofont": 1,
    "fontsize": 2,
    "selectfont": 0,
    "usefont": 4,
    # You might also add:
    "geometry": 1,  # \geometry{margin=1in}
    "newgeometry": 1,
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
    "pdfmapline": "{",
    # Page-related formatting
    # Style commands
    "pagestyle": 1,
    "newpagestyle": 2,
    "renewpagestyle": 2,
    "thispagestyle": 1,
    "urlstyle": 1,
    "theoremstyle": 1,
    "bibliographystyle": 1,
    "documentstyle": 1,
    "setcitestyle": 1,
    # test style commands
    "textstyle": 0,
    "displaystyle": 0,
    "mathstyle": 0,
    "scriptstyle": 0,
    "scriptscriptstyle": 0,
    # other
    "enlargethispage": 1,
    "pagecolor": "*{",
    "centering": 0,
    "raggedright": 0,
    "raggedleft": 0,
    "raggedtop": 0,
    "raggedbottom": 0,
    "nohyphens": 0,
    "allowdisplaybreaks": 0,
    "samepage": 0,
    "thepage": 0,
    "indent": 0,
    "noindent": 0,
    "clearpage": 0,
    "cleardoublepage": 0,
    "nopagebreak": 0,
    "nobreak": 0,
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
    # lists and items
    "lstset": "{",
    "setlist": "[{",
    "setitemize": "[{",
    "setenumerate": "[{",
    "setdescription": "[{",
    # toolset/palette
    "mathtoolsset": "[{",
    # \kern, which is technically spacing but more like a length between characters. so ignore
    "kern": "d",
    # setup
    "hypersetup": "[{",
    "captionsetup": "[{",
    #
    "tracinglostchars": "=i",
    "tracingpages": "=i",
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
    # leavemode
    "leavevmode": 0,  # % vertical mode → horizontal mode
    "strut": 0,
    # hyphenchar
    "hyphenchar": "\\=i",
    # @onlypreamble is a special command that is used to ignore commands that are only allowed in the preamble
    "@onlypreamble": "{",
    # fancyhead/headers
    "fancyhead": "[{",
    "fancyheadoffset": "[{",
    "rhead": "[{",
    "chead": "[{",
    "lhead": "[{",
    "rfoot": "[{",
    "cfoot": "[{",
    "lfoot": "[{",
    # ligatures
    "DisableLigatures": "[{",
    # makeperpage
    "MakePerPage": "{",
    # rcs
    "rcsInfo": "{",
    # todo
    "todo": "[{",
    "listoftodos": 0,
    "listoftheorems": 0,
    # error lines
    "errorcontextlines": "=i",
    # mag
    "mag": "=i",
    "magstep": "i",
    # eps
    "epsfxsize": "=d",
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
    "getpagerefnumber": 1,
    # line numbers
    "linenumbers": 0,
    "linesnumbered": 0,
    "linenomath": 0,
    "endlinenomath": 0,
    "modulolinenumbers": "[",
    "resetlinenumber": 0,
    # bib
    "printbibliography": 0,
    "renewbibmacro": "{{",
    # datetime
    "date": "{",
    "today": 0,
    # counter
    "AddEnumerateCounter": 3,
    # newlabel
    "newlabel": 2,
    # width/height/depth standalone
    "width": 0,
    "height": 0,
    "depth": 0,
}


def vrule_hrule_handler(expander: ExpanderCore, token: Token):
    seen_keywords = set()
    dimensions = ["width", "height", "depth"]
    while True:
        expander.skip_whitespace()
        found_dimension = False
        for dim in dimensions:
            if dim not in seen_keywords and expander.parse_keyword(f"{dim} "):
                expander.parse_dimensions()
                seen_keywords.add(dim)
                found_dimension = True
                break
        if not found_dimension:
            break
    return []


def newline_handler(expander: ExpanderCore, token: Token):
    # parse out any e.g. \\[0.5em]
    space_cnt = expander.skip_whitespace_not_eol()
    if not expander.parse_bracket_as_tokens():
        # i.e. no \\ ... [0.5em]
        # push back the space tokens
        expander.push_text(" " * space_cnt)
    return [token]


def mathpalette_handler(expander: ExpanderCore, token: Token):
    toks1 = expander.parse_immediate_token(skip_whitespace=False, expand=False)
    if not toks1:
        expander.logger.warning(
            f"Warning: \\mathpalette expected argument but found nothing"
        )
        return None

    # arbitrarily push a displaystyle token to stream
    style_token = Token(TokenType.CONTROL_SEQUENCE, value="displaystyle")
    expander.push_tokens(toks1 + [style_token])
    return []


def is_dollar_token(tok: Token) -> bool:
    return tok.type == TokenType.MATH_SHIFT_INLINE and tok.value == "$"


def rcsinfo_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    tok = expander.peek()
    if not tok or not is_dollar_token(tok):
        expander.logger.info(
            f"Warning: \\rcsInfo expected math shift inline but found {tok}"
        )
        return None
    expander.consume()
    tokens = expander.parse_tokens_until(is_dollar_token, consume_predicate=True)
    # ignore?
    return []


def big_handler(expander: ExpanderCore, token: Token):
    r"""
    It makes the following delimiter (like (, [, {, |, etc.) slightly larger than normal text size, but not as large as \Big, \bigg, or \Bigg

    We just ignore this command
    """
    # tokens = expander.parse_immediate_token(skip_whitespace=True, expand=True)
    return []


def register_ignore_format_handlers(expander: ExpanderCore):
    """Register all formatting-related command handlers"""
    register_ignore_handlers_util(expander, formatting_patterns, expand=False)
    register_ignore_handlers_util(expander, content_formatting_patterns, expand=False)
    expander.register_handler(r"\vrule", vrule_hrule_handler, is_global=True)
    expander.register_handler(r"\hrule", vrule_hrule_handler, is_global=True)
    expander.register_handler(r"\mathpalette", mathpalette_handler, is_global=True)
    expander.register_handler(r"\rcsInfo", rcsinfo_handler, is_global=True)
    expander.register_handler("\\", newline_handler, is_global=True)

    for big in ["big", "Big", "bigg", "Bigg"]:
        expander.register_handler(big, big_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_ignore_format_handlers(expander)

    # # Test some formatting commands
    # out1 = expander.expand(r"\floatname{figure}{Fig.}")
    # out2 = expander.expand(r"\pagestyle{fancy}")
    # out3 = expander.expand(
    #     r"\titleformat{\section}{\normalfont\Large\bfseries}{\thesection}{1em}{}"
    # )
    # out4 = expander.expand(r"\vrule height 2pt depth -1.6pt width 23pt")

    out = expander.expand(r"\rcsInfo $Id: xxx$")
