from typing import List, Optional
from latex2json.latex_maps.dimensions import dimension_to_scaled_points
from latex2json.tokens.types import Token
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.if_else.base_if import process_if_else_block


def ifdim_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""
    Handles \ifdim command which compares two dimensions.
    Format: \ifdim dim1 <relation> dim2
    where relation is <, =, or >
    """
    # Parse first dimension
    expander.skip_whitespace()
    val1 = expander.parse_dimensions()
    if val1 is None:
        expander.logger.warning("Warning: \\ifdim expects a dimension")
        return None

    # Parse relation operator
    expander.skip_whitespace()
    tok = expander.consume()  # greedy consume (not peek)
    if tok is None:
        expander.logger.warning("Warning: \\ifdim expects a relation operator")
        return None

    relation = tok.value
    if relation not in ["<", "=", ">"]:
        expander.logger.warning("Warning: \\ifdim expects <, =, or > operator")
        return None

    # Parse second dimension
    expander.skip_whitespace()
    val2 = expander.parse_dimensions()
    if val2 is None:
        expander.logger.warning("Warning: \\ifdim expects a second dimension")
        return None

    is_true = False
    if relation == "<":
        is_true = val1 < val2
    elif relation == "=":
        is_true = val1 == val2
    else:  # >
        is_true = val1 > val2

    return process_if_else_block(expander, is_true)


def register_ifdim(expander: ExpanderCore):
    expander.register_handler("\\ifdim", ifdim_handler, is_global=True)


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
