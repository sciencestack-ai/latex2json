r"""
Commands to ignore

See handler_utils.py for the argument specification format.

Argument Specification Format:
- Integer (e.g., 1, 2): Number of braced blocks to parse e.g. 2 = "{{"
- String: Character-based argument specification where:
  * : star (asterisk)
  [ : optional bracket argument
  { : required brace argument or immediate token
  ( : optional parenthesis argument
  = : equals sign
  \\ : command/control sequence
  f : parse float
  d : parse dimension
  i : parse integer

Examples:
  "pageheight": 1           → \pageheight{arg}
  "titleformat": "*{[{{{{" → \titleformat*{arg}[opt]{arg}{arg}{arg}{arg}
  "pdfoutput": "=i"         → \pdfoutput=123
  "hyphenchar": "\\=d"      → \hyphenchar\font=1.23pt

"""

formatting_patterns = {
    "makesavenoteenv": 1,
    "setminted": 1,
    "CJKnospace": 0,
    "bibpunct": 6,
    "newcolumntype": "{[{",
    "addpenalty": "{",
    "@parboxrestore": 0,
    # language/localization
    "extrasenglish": 0,
    "selectlanguage": "{",
    "pageheight": 1,
    "pagewidth": 1,
    "NeedsTeXFormat": 1,
    "looseness": "=i",
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
    # You might also add:
    "geometry": 1,  # \geometry{margin=1in}
    "newgeometry": 1,
    "setstretch": 1,  # \setstretch{1.5} - line spacing
    # Package processing
    "ExecuteOptions": 1,
    "ProcessOptions": 0,  # Actually takes no arguments
    "ExecuteBibliographyOptions": 1,
    # pdf options
    "pdfstringdefDisableCommands": "{",
    "pdfinfo": "{",
    "pdfinfoomitdate": "{",
    "pdftrailerid": "{",
    "pdfoutput": "=i",
    "pdfsuppresswarningpagegroup": "=i",
    "pdfoptionpdfminorversion": "i",
    "pdfmapline": "{",
    "suppressfloats": "[",
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
    "center": 0,
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
    "balance": 0,
    "flushbottom": 0,
    "flushleft": 0,
    "flushright": 0,
    "flushtop": 0,
    # lists and items
    "lstset": "{",
    "lstdefinestyle": "{{",
    "setlist": "[{",
    "setitemize": "[{",
    "setenumerate": "[{",
    "setdescription": "[{",
    # toolset/palette
    "mathtoolsset": "[{",
    "newtagform": "{[{{",
    "usetagform": "{",
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
    "foreignlanguage": "{",  # \foreignlanguage{language}{text}, but only strip out \foreignlanguage{language}, preserving {text}
    # class/MSC
    "subjclass": "[{",
    "MSC": "{",
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
    # hyphenchar/skewchar
    "hyphenchar": "\\=i",
    "skewchar": "\\=i",
    # @onlypreamble is a special command that is used to ignore commands that are only allowed in the preamble
    "@onlypreamble": "{",
    # fancyhead/headers
    "fancyhf": "[{",
    "fancyhead": "[{",
    "fancyfoot": "[{",
    "fancyheadoffset": "[{",
    "fancyfootoffset": "[{",
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
    "magnification": "=i",
    # unskips/postskips
    "unskip": 0,
    "theorempostskipamount": 0,
    # frenchspacing
    "frenchspacing": 0,
    "singlespacing": 0,
    "doublespacing": 0,
    "onehalfspacing": 0,
    "nonfrenchspacing": 0,
    # psfrag (ignoring this will affect the ps output e.g. eps)
    "psfrag": "{{",
    # newsymbol (creating a new math symbol.., should add support in future)
    "newsymbol": "\\i",
    # other
    "tolerance": "=i",
    "delimitershortfall": "=d",
    # mathversion
    "mathversion": "{",
    "@nocounterr": 0,
    # metadata
    "DocumentMetadata": "{",
    "refpage": 0,
    "afterpage": "{",
    # kernel
    "@currenvir": 0,
    # hyperref
    "Hy@MakeCurrentHref": "{",
    "Hy@linkcounter": 0,
    "Hy@raisedlink": "{",
    "hyper@anchorstart": "{",
    "hyper@anchorend": 0,
    "@currentHref": 0,
    # end...
    "endfoot": 0,
    "endhead": 0,
    "endlastfoot": 0,
    "endlasthead": 0,
    "endfirsthead": 0,
    "endfirstfoot": 0,
    # stackengine
    "@STRT": 0,
}

content_formatting_patterns = {
    # row
    "rowfont": "{",
    "RowStyle": "{",
    # pstricks (old)
    "newgray": "{{",
    "psset": "{",
    "SpecialCoor": 0,
    # matter
    "frontmatter": 0,
    "mainmatter": 0,
    "backmatter": 0,
    # math
    "everymath": 1,
    # title
    "maketitle": 0,
    "@title": 0,
    "titlecontents": "{[{{{{[",
    # files
    "listfiles": 0,
    # TOCs
    "localtableofcontents": 0,
    "tableofcontents": 0,
    "etocsettocstyle": 2,
    "etocsetstyle": 5,
    "@tocline": 5,
    "@tocpagenum": 1,
    "@dottedtocline": 3,
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
    "printbibliography": "[",
    "renewbibmacro": "{{",
    # datetime
    "date": "{",
    "day": 0,
    "month": 0,
    "year": 0,
    "today": 0,
    # counter
    "AddEnumerateCounter": 3,
    # newlabel
    "newlabel": 2,
    # width/height/depth standalone
    "width": 0,
    "height": 0,
    "depth": 0,
    # mark
    "markboth": 2,
    "markright": 1,
    "markleft": 1,
    # marginpar
    "marginpar": 1,
    # glossary
    "makeglossary": 0,
    "printglossary": 0,
    "newglossaryentry": "{{",
}

separator_patterns = {
    "hline": 0,
    "vline": 0,
    "hrulefill": 0,
    "centerline": 0,
    "cline": "{",
    "topsep": 0,
    "parsep": 0,
    "partopsep": 0,
    "labelsep": "{",
    "midrule": "[",
    "toprule": "[",
    "bottomrule": "[",
    "cmidrule": "([{",
    "hdashline": "[",
    "cdashline": "{",
    "specialrule": "{{{",
    "addlinespace": "[",
    "rule": "[{{",
    "hrule": 0,
    "morecmidrules": 0,
    "fboxsep": "{",
    "Xhline": "{",
    "tabcolsep": 0,
    "colrule": 0,
    "noalign": 0,
    "endfirsthead": 0,
}

font_awesome_patterns = {
    "faGithub": 0,
    "faGithubAlt": 0,
}

IGNORE_PATTERNS = (
    separator_patterns
    | formatting_patterns
    | content_formatting_patterns
    | font_awesome_patterns
)
