from typing import List


def parse_number_str_to_float(sequence: str) -> float:
    minus_count = sequence.count("-")
    digits = sequence.lstrip("+-")
    multiplier = -1 if minus_count % 2 == 1 else 1
    if not digits:
        return multiplier
    return multiplier * float(digits)
