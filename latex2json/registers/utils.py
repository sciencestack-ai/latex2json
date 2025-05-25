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
