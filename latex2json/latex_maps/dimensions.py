# Conversion factors to scaled points (sp)
# 1 pt = 65536 sp (by definition)
# Other conversions are calculated relative to points
from typing import Optional


LATEX_DIMENSION_UNITS = {
    "pt": 65536,  # Point (1 pt = 65536 sp)
    "mm": 186467,  # Millimeter (1 mm ≈ 2.845275 pt)
    "cm": 1864667,  # Centimeter (1 cm = 10 mm)
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
