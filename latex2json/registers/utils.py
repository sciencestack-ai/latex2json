from typing import Optional


def int_to_roman(num: int, lowercase: bool = True) -> str:
    """Convert integer to Roman numerals

    Args:
        num: Integer to convert
        lowercase: Whether to return lowercase numerals

    Returns:
        String representation in Roman numerals
    """
    if num <= 0:
        return ""

    values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    literals = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]

    result = ""
    for i, value in enumerate(values):
        count = num // value
        if count:
            result += literals[i] * count
            num -= value * count

    return result.lower() if lowercase else result


def int_to_alpha(num: int, lowercase: bool = True) -> str:
    """Convert integer to alphabetic representation (a-z, aa-zz etc)

    Args:
        num: Integer to convert
        lowercase: Whether to return lowercase letters

    Returns:
        String representation using letters
    """
    if num <= 0:
        return ""

    result = ""
    while num > 0:
        num -= 1  # Make it 0-based
        result = chr((ord("a") if lowercase else ord("A")) + (num % 26)) + result
        num //= 26

    return result


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
    unit = unit.strip()
    if not is_dimension_unit(unit):
        return None
    return int(value * LATEX_DIMENSION_UNITS[unit])
