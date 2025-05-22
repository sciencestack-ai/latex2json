from typing import List, Optional
from latex2json.latex_maps.dimensions import dimension_to_scaled_points
from latex2json.tokens.types import Token
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.if_else.base_if import IfMacro


def evaluate_ifdim(
    expander: ExpanderCore, token: Token
) -> tuple[bool | None, str | None]:
    # Parse first dimension
    expander.skip_whitespace()
    val1 = expander.parse_dimensions()
    if val1 is None:
        return None, "\\ifdim expects a dimension"

    # Parse relation operator
    expander.skip_whitespace()
    tok = expander.consume()  # greedy consume (not peek)
    if tok is None:
        return None, "\\ifdim expects a relation operator"

    relation = tok.value
    if relation not in ["<", "=", ">"]:
        return None, "\\ifdim expects <, =, or > operator"

    # Parse second dimension
    expander.skip_whitespace()
    val2 = expander.parse_dimensions()
    if val2 is None:
        return None, "\\ifdim expects a second dimension"

    is_true = False
    if relation == "<":
        is_true = val1 < val2
    elif relation == "=":
        is_true = val1 == val2
    else:  # >
        is_true = val1 > val2

    return is_true, None


def register_ifdim(expander: ExpanderCore):
    expander.register_macro("\\ifdim", IfMacro("ifdim", evaluate_ifdim), is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_ifdim(expander)
    test_with_registers = r"""
    \dimen0=5pt
    \dimen1=3pt
    \ifdim\dimen0>\dimen1
        TRUE
    \else
        FALSE
    \fi
    """.strip()

    out = expander.expand(test_with_registers)
    print(out)
