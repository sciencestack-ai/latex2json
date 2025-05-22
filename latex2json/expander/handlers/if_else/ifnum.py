from typing import List, Optional
from latex2json.tokens.types import Token
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.if_else.base_if import process_if_else_block


def ifnum_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""
    Handles \ifnum command which compares two numbers.
    Format: \ifnum num1 <relation> num2
    where relation is <, =, or >
    """
    # Parse first number
    expander.skip_whitespace()
    num1 = expander.parse_integer()
    if num1 is None:
        expander.logger.warning("Warning: \\ifnum expects a number")
        return None

    # Parse relation operator
    expander.skip_whitespace()
    tok = expander.consume()  # greedy consume (not peek)
    if tok is None:
        expander.logger.warning("Warning: \\ifnum expects a relation operator")
        return None

    relation = tok.value
    if relation not in ["<", "=", ">"]:
        expander.logger.warning("Warning: \\ifnum expects <, =, or > operator")
        return None

    # Parse second number
    expander.skip_whitespace()
    num2 = expander.parse_integer()
    if num2 is None:
        expander.logger.warning("Warning: \\ifnum expects a second number")
        return None

    # Compare numbers based on relation
    is_true = False
    if relation == "<":
        is_true = num1 < num2
    elif relation == "=":
        is_true = num1 == num2
    else:  # >
        is_true = num1 > num2

    return process_if_else_block(expander, is_true)


def register_ifnum(expander: ExpanderCore):
    expander.register_handler("\\ifnum", ifnum_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    out = expander.expand(r"\ifnum 1 < 0 TRUE \else FALSE \fi")
    print(out)
