BUILTIN_DIMENSIONS = [
    "displaywidth",
    "displayheight",
    "maxdimen",
    "sublargesize",
    # Page layout dimensions
    "textwidth",  # Width of text area
    "textheight",  # Height of text area
    "paperwidth",  # Total page width
    "paperheight",  # Total page height
    "linewidth",
    "columnwidth",  # Width of column (in multicolumn)
    "columnseprule",  # Width of rule between columns
    "marginparwidth",  # Width of margin notes
    "marginparpush",
    "oddsidemargin",  # Left margin on odd pages
    "evensidemargin",  # Left margin on even pages
    "topmargin",  # Top margin
    "headheight",  # Height of page headers
    "headwidth",
    "hoffset",  # Horizontal page offset
    "voffset",  # Vertical page offset
    "unitlength",  # Unit length for picture environment
    # Paragraph formatting
    "parindent",  # Paragraph indentation
    # List formatting
    "leftmargin",  # Left margin in lists
    "rightmargin",  # Right margin in lists
    "listparindent",  # Paragraph indent within list items
    "itemindent",  # Additional indent for item bodies
    "labelwidth",  # Width allocated for item labels
    # Table formatting
    "arrayrulewidth",  # Thickness of table rules
    "heavyrulewidth",
    "extrarowheight",  # Extra height added to table rows
    # Math formatting
    "jot",  # Extra space in eqnarray
    "mathsurround",  # Space around inline math
    # Box dimensions (for measuring)
    "fboxrule",  # Thickness of frame box rules
    # Sectioning
    "bibindent",  # Indentation in bibliography
    # Page breaking
    "maxdepth",  # Maximum depth of page
    "splitmaxdepth",
    "prevdepth",
    # Emergency stretching
    "emergencystretch",  # Extra stretch in emergency
    # Hyphenation
    "hfuzz",  # Tolerance for overfull hboxes
    "vfuzz",  # Tolerance for overfull vboxes
    "overfullrule",  # Width of overfull rule marker
    # hsize/vsize
    "hsize",
    "vsize",
    # @
    "p@",
    "z@",
    "dimen@",
    "@tempdima",
    "@tempdimb",
    "@tempdimc",
    # pdfpage dimensions
    "pdfpagewidth",
    "pdfpageheight",
]

for incr in ["i", "ii", "iii", "iv", "v"]:
    BUILTIN_DIMENSIONS.append(f"leftmargin{incr}")
    BUILTIN_DIMENSIONS.append(f"rightmargin{incr}")
