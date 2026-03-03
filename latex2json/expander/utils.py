from typing import Callable, List, Optional

from latex2json.tokens.types import Token, TokenType


RELAX_TOKEN = Token(TokenType.CONTROL_SEQUENCE, "relax")


def is_token_command_name(tok: Token, command_name: str) -> bool:
    return tok.type == TokenType.CONTROL_SEQUENCE and tok.value == command_name


def integer_tok_cur_str_predicate(tok: Token, cur_str: str) -> bool:
    if tok.value.isdigit() or tok.value in "ABCDEF":
        return True
    has_digit = any(c.isdigit() or c in "ABCDEF" for c in cur_str)
    # allows for hex + octal + ascii + sign
    if not has_digit and tok.value in ["+", "-", " ", "'", '"', "`"]:
        return True
    return False


def parse_number_str_to_float(sequence: str) -> Optional[float]:
    # replace comma with dot for decimal point (TeX uses comma for decimals too)
    sequence = sequence.replace(",", ".").strip()
    # if only a decimal point, return None
    if not sequence or sequence == ".":
        return None

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
