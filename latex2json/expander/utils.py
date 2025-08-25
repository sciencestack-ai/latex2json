from typing import List


def parse_number_str_to_float(sequence: str) -> float:
    # replace comma with dot for decimal point (TeX uses comma for decimals too)
    sequence = sequence.replace(",", ".")

    # Count leading +/- signs (TeX allows multiple)
    sign = 1
    i = 0
    while i < len(sequence) and sequence[i] in "+-":
        if sequence[i] == "-":
            sign *= -1
        i += 1
    core = sequence[i:]

    if not core:
        # return the sign
        return sign

    # Now parse core as number
    try:
        N = len(core)
        if N > 1 and core.startswith("'"):  # Octal
            value = int(core[1:], 8)
        elif N > 1 and core.startswith('"'):  # Hex
            value = int(core[1:], 16)
        elif N > 1 and core.startswith("`"):  # ASCII
            value = ord(core[1])
        else:
            value = float(core)  # Regular float or int string
    except ValueError:
        return 0

    return sign * value


if __name__ == "__main__":
    print(parse_number_str_to_float("42"))  # 42.0
    print(parse_number_str_to_float("-42"))  # -42.0
    print(parse_number_str_to_float("--42"))  # 42.0
    print(parse_number_str_to_float("'101"))  # 65.0
    print(parse_number_str_to_float("-'101"))  # -65.0
    print(parse_number_str_to_float("`A"))  # 65.0
    print(parse_number_str_to_float("--`A"))  # 65.0
    print(parse_number_str_to_float('"41'))  # 65.0
