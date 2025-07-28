from typing import List, Optional
from latex2json.tokens.types import Token
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.if_else.base_if import IfMacro
from latex2json.tokens.utils import strip_whitespace_tokens


def evaluate_ifnum(
    expander: ExpanderCore, token: Token
) -> tuple[bool | None, str | None]:
    # Parse first number
    expander.skip_whitespace()
    num1 = expander.parse_integer()
    # if num1 is None:
    #     return None, f"\\ifnum expects a number, found {expander.peek()}"

    # Parse relation operator
    expander.skip_whitespace()
    relation_tok = expander.consume()  # greedy consume (not peek)
    # if tok is None:
    #     return None, "\\ifnum expects a relation operator"

    # Parse second number
    expander.skip_whitespace()
    num2 = expander.parse_integer()

    if num1 is None:
        return None, "\\ifnum expects a first number"
    if relation_tok is None:
        return None, "\\ifnum expects a relation operator"
    relation = relation_tok.value
    if relation not in ["<", "=", ">"]:
        return None, "\\ifnum expects <, =, or > operator"
    if num2 is None:
        return None, "\\ifnum expects a second number"

    # Compare numbers based on relation
    is_true = False
    if relation == "<":
        is_true = num1 < num2
    elif relation == "=":
        is_true = num1 == num2
    else:  # >
        is_true = num1 > num2

    return is_true, None


def register_ifnum(expander: ExpanderCore):
    expander.register_macro("\\ifnum", IfMacro("ifnum", evaluate_ifnum), is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    out = expander.expand(r"\ifnum\ifnum 1 > 0 1 \else 0 \fi > 0 TRUE \else FALSE \fi")
    # print(out)

    test_nested = r"""
    \ifnum 1 > 0
        \ifnum 1 > 0 
            TRUE
        \else
            FALSE
        \fi
    \fi
    """.strip()
    out = expander.expand(test_nested)
    out = strip_whitespace_tokens(out)
