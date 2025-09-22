BUILTIN_DIMENSIONS = [
    "displaywidth",
    "displayheight",
    "maxdimen",
    # Page layout dimensions
    "textwidth",  # Width of text area
    "textheight",  # Height of text area
    "paperwidth",  # Total page width
    "paperheight",  # Total page height
    "linewidth",
    "columnwidth",  # Width of column (in multicolumn)
    "columnsep",  # Space between columns
    "columnseprule",  # Width of rule between columns
    "marginparwidth",  # Width of margin notes
    "marginparsep",  # Space between text and margin notes
    "oddsidemargin",  # Left margin on odd pages
    "evensidemargin",  # Left margin on even pages
    "topmargin",  # Top margin
    "headheight",  # Height of page headers
    "headwidth",
    "headsep",  # Space between header and text
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
    "labelsep",  # Space between label and item text
    "labelwidth",  # Width allocated for item labels
    # Table formatting
    "arrayrulewidth",  # Thickness of table rules
    "heavyrulewidth",
    "arraycolsep",  # Column separation in array environment
    "tabcolsep",  # Column separation in tabular environment
    "doublerulesep",  # Space between double rules
    "extrarowheight",  # Extra height added to table rows
    # Math formatting
    "jot",  # Extra space in eqnarray
    "mathsurround",  # Space around inline math
    # Float formatting
    "floatsep",  # Space between floats
    "textfloatsep",  # Space between floats and text
    "intextsep",  # Space around here floats
    "dblfloatsep",  # Space between double-column floats
    "dbltextfloatsep",  # Space between double floats and text
    # Footnote formatting
    "footnotesep",  # Space between footnote rule and text
    # Box dimensions (for measuring)
    "fboxrule",  # Thickness of frame box rules
    "fboxsep",  # Space between frame and contents
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
