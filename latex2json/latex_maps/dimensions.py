# Conversion factors to scaled points (sp)
# 1 pt = 65536 sp (by definition)
# Other conversions are calculated relative to points
from typing import Optional

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


LATEX_DIMENSION_UNITS = {
    "pt": 65536,  # Point (1 pt = 65536 sp)
    "mm": 186467,  # Millimeter (1 mm ≈ 2.845275 pt)
    "cm": 1864667,  # Centimeter (1 cm = 10 mm)
    "truecm": 1864667,  #
    "in": 4736286,  # Inch (1 in = 72.27 pt)
    "ex": 295245,  # Roughly the height of lowercase 'x' (≈ 4.5 pt)
    "em": 655360,  # Roughly width of 'M' (≈ 10 pt)
    "mu": 36409,  # Math unit (1/18 em)
    "sp": 1,  # Scaled point (base unit)
    "bp": 65782,  # Big point (1/72 inch)
    "pc": 786432,  # Pica (12 pt)
    "dd": 70124,  # Didot point (≈ 1.07 pt)
    "cc": 841488,  # Cicero (12 didot points)
    "nd": 70124,  # New Didot (≈ 1.07 pt)
    "nc": 841488,  # New Cicero (12 new didot)
    "px": 65536,  # Pixel (assumed same as pt for conversion)
    "zw": 655360,  # Ideographic width (≈ 10 pt)
    "zh": 655360,  # Ideographic height (≈ 10 pt)
    "Q": 46617,  # Quarter millimeter (0.25 mm)
    "vw": 65536,  # Viewport width (treated as pt for conversion)
    "vh": 65536,  # Viewport height (treated as pt for conversion)
    # Infinite glue units (fil units) - using large integers instead of infinity
    "fil": 2**30,  # First order infinity
    "fill": 2**31,  # Second order infinity (larger than fil)
    "filll": 2**32,  # Third order infinity (larger than fill)
}


def is_dimension_unit(unit: str) -> bool:
    """Check if a string is a valid LaTeX dimension unit."""
    return unit in LATEX_DIMENSION_UNITS


def dimension_to_scaled_points(
    value: float, unit: Optional[str] = None
) -> Optional[int]:
    """Convert a dimension value from given unit to scaled points.

    Args:
        value: The numeric value to convert
        unit: The unit to convert from

    Returns:
        The equivalent value in scaled points (sp)

    Raises:
        KeyError: If the unit is not a valid LaTeX dimension unit
    """
    if not unit or unit.isspace():
        return int(value)
    if not is_dimension_unit(unit):
        return None
    return int(value * LATEX_DIMENSION_UNITS[unit])
