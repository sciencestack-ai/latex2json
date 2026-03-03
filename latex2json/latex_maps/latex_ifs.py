"""
Default values for LaTeX formatting conditionals.
These behave like \newif conditionals with setter commands.
"""

LATEX_IFS = {
    # Standard LaTeX formatting conditionals
    "@minipage": False,
    "@twoside": False,
    "@onecolumn": True,
    "@twocolumn": False,
    "@titlepage": False,
    "@openright": False,
    "@mainmatter": False,
    "@restonecol": False,
    "@inlabel": False,
    "@inbib": False,
    "@filesw": False,
    "@newlist": False,
    "hmode": True,
    "vmode": False,
    "inner": False,
    "pdf": True,  # set to True since LaTeX mostly compiles to pdf
    # Engine detection conditionals (iftex package)
    "pdftex": True,  # assume pdfTeX by default
    "luatex": False,
    "luahbtex": False,
    "xetex": False,
    "ptex": False,
    "uptex": False,
    "etex": True,  # eTeX extensions are always available in modern TeX
    "TUTeX": False,
    # Internal LaTeX conditionals
    "@tempswa": False,
    "@ignore": False,
    "@endpe": False,
}
