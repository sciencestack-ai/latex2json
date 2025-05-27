from typing import List


def parse_number_str_to_float(sequence: str) -> float:
    minus_count = sequence.count("-")
    digits = sequence.lstrip("+-")
    if not digits:
        return None
    return -float(digits) if minus_count % 2 == 1 else float(digits)
