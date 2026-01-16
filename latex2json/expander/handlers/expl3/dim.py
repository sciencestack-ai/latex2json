r"""
expl3 dimension (dim) handlers.

Handles \dim_new:N, \dim_set:Nn, \dim_add:Nn, \dim_use:N,
\dim_compare:nTF, \dim_eval:n, etc.

Dimension values are stored in a dedicated dictionary with (value, unit) tuples.
This provides proper formatting when outputting values (e.g., "10.0pt" not raw sp).
"""

import re
from typing import Dict, List, Optional, Tuple

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


# Dedicated storage for dimension values: {var_name: (value, unit)}
# This allows proper formatting of output (e.g., "10.0pt")
_dim_store: Dict[str, Tuple[float, str]] = {}


def _get_var_name(var: Token) -> str:
    """Get the variable name from a token."""
    return var.value


def _get_dim(name: str) -> Tuple[float, str]:
    """Get dimension value from store, defaulting to (0.0, 'pt')."""
    return _dim_store.get(name, (0.0, 'pt'))


def _set_dim(name: str, value: float, unit: str) -> None:
    """Set dimension value in store."""
    _dim_store[name] = (value, unit)


def _format_dim(value: float, unit: str) -> str:
    """Format dimension value for output."""
    if value == int(value):
        return f"{int(value)}{unit}"
    return f"{value}{unit}"


def dim_new_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \dim_new:N \l_my_dim
    Create a new dimension variable initialized to 0pt.
    """
    expander.skip_whitespace()
    var = expander.consume()
    if var:
        name = _get_var_name(var)
        _set_dim(name, 0.0, 'pt')
    return []


def dim_set_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \dim_set:Nn \l_my_dim {10pt}
    Set a dimension variable to a value.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    value_tokens = expander.parse_brace_as_tokens() or []
    value_str = "".join(t.value for t in value_tokens).strip()

    if var:
        name = _get_var_name(var)
        parsed = _parse_dim_value(value_str)
        if parsed:
            _set_dim(name, parsed[0], parsed[1])
    return []


def dim_gset_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \dim_gset:Nn \g_my_dim {10pt}
    Globally set a dimension variable.
    Note: In our implementation, all dim storage is global by nature.
    """
    return dim_set_handler(expander, _token)


def dim_add_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \dim_add:Nn \l_my_dim {5pt}
    Add a value to a dimension variable.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    value_tokens = expander.parse_brace_as_tokens() or []
    value_str = "".join(t.value for t in value_tokens).strip()

    if var:
        name = _get_var_name(var)
        current_val, current_unit = _get_dim(name)
        parsed = _parse_dim_value(value_str)
        if parsed:
            add_val, add_unit = parsed
            # Convert to pt for addition, then back
            current_pt = _to_pt(current_val, current_unit)
            add_pt = _to_pt(add_val, add_unit)
            if current_pt is not None and add_pt is not None:
                result_pt = current_pt + add_pt
                _set_dim(name, result_pt, 'pt')
    return []


def dim_sub_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \dim_sub:Nn \l_my_dim {5pt}
    Subtract a value from a dimension variable.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    value_tokens = expander.parse_brace_as_tokens() or []
    value_str = "".join(t.value for t in value_tokens).strip()

    if var:
        name = _get_var_name(var)
        current_val, current_unit = _get_dim(name)
        parsed = _parse_dim_value(value_str)
        if parsed:
            sub_val, sub_unit = parsed
            current_pt = _to_pt(current_val, current_unit)
            sub_pt = _to_pt(sub_val, sub_unit)
            if current_pt is not None and sub_pt is not None:
                result_pt = current_pt - sub_pt
                _set_dim(name, result_pt, 'pt')
    return []


def dim_zero_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \dim_zero:N \l_my_dim
    Set a dimension variable to 0pt.
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        name = _get_var_name(var)
        _set_dim(name, 0.0, 'pt')
    return []


def dim_use_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \dim_use:N \l_my_dim
    Output the value of a dimension variable.
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        name = _get_var_name(var)
        value, unit = _get_dim(name)
        return expander.convert_str_to_tokens(_format_dim(value, unit))
    return []


def dim_eval_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \dim_eval:n { 10pt + 5pt }  ->  15pt

    Note: We do simplified evaluation - just return the expression for now
    since proper dimension arithmetic requires tracking units.
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    # Try to evaluate simple dimension arithmetic
    result = _safe_eval_dim(expr_str)
    if result is not None:
        return expander.convert_str_to_tokens(result)
    # Fall back to returning the expression
    return expander.convert_str_to_tokens(expr_str)


def _parse_dim_value(s: str) -> Optional[tuple]:
    """Parse a dimension string into (value, unit). Returns None if invalid."""
    s = s.strip()
    # Match number followed by unit
    match = re.match(r'^([+-]?\d*\.?\d+)\s*(pt|pc|in|bp|cm|mm|dd|cc|sp|ex|em)?$', s)
    if match:
        value = float(match.group(1))
        unit = match.group(2) or 'pt'
        return (value, unit)
    return None


def _safe_eval_dim(expr_str: str) -> Optional[str]:
    """Safely evaluate dimension arithmetic expression."""
    # Simple case: just a dimension value
    parsed = _parse_dim_value(expr_str)
    if parsed:
        value, unit = parsed
        if value == int(value):
            return f"{int(value)}{unit}"
        return f"{value}{unit}"

    # Try simple addition/subtraction of dimensions with same unit
    # Pattern: value1unit op value2unit
    match = re.match(
        r'^([+-]?\d*\.?\d+)\s*(pt|pc|in|bp|cm|mm|dd|cc|sp|ex|em)?\s*'
        r'([+-])\s*'
        r'([+-]?\d*\.?\d+)\s*(pt|pc|in|bp|cm|mm|dd|cc|sp|ex|em)?$',
        expr_str
    )
    if match:
        val1 = float(match.group(1))
        unit1 = match.group(2) or 'pt'
        op = match.group(3)
        val2 = float(match.group(4))
        unit2 = match.group(5) or unit1

        if unit1 == unit2:
            if op == '+':
                result = val1 + val2
            else:
                result = val1 - val2
            if result == int(result):
                return f"{int(result)}{unit1}"
            return f"{result}{unit1}"

    return None


def dim_compare_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \dim_compare:nTF { 10pt > 5pt } {true} {false}

    Supports: <, >, =, <=, >=, !=
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    result = _eval_dim_compare(expr_str)
    if result:
        expander.push_tokens(true_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def dim_compare_T_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \dim_compare:nT { 10pt > 5pt } {true}
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    result = _eval_dim_compare(expr_str)
    if result:
        expander.push_tokens(true_branch)
    return []


def dim_compare_F_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \dim_compare:nF { 10pt > 5pt } {false}
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    result = _eval_dim_compare(expr_str)
    if not result:
        expander.push_tokens(false_branch)
    return []


def _eval_dim_compare(expr_str: str) -> bool:
    """Evaluate dimension comparison expression."""
    # Normalize operators
    expr_str = expr_str.replace(">=", " >= ").replace("<=", " <= ")
    expr_str = expr_str.replace("!=", " != ").replace("==", " = ")

    # Try different operators
    for op, func in [
        (">=", lambda a, b: a >= b),
        ("<=", lambda a, b: a <= b),
        ("!=", lambda a, b: a != b),
        (">", lambda a, b: a > b),
        ("<", lambda a, b: a < b),
        ("=", lambda a, b: abs(a - b) < 0.001),
    ]:
        if op in expr_str:
            parts = expr_str.split(op, 1)
            if len(parts) == 2:
                left_parsed = _parse_dim_value(parts[0].strip())
                right_parsed = _parse_dim_value(parts[1].strip())
                if left_parsed and right_parsed:
                    # Convert to common unit (pt) for comparison
                    left_pt = _to_pt(left_parsed[0], left_parsed[1])
                    right_pt = _to_pt(right_parsed[0], right_parsed[1])
                    if left_pt is not None and right_pt is not None:
                        return func(left_pt, right_pt)
    return False


def _to_pt(value: float, unit: str) -> Optional[float]:
    """Convert dimension value to points."""
    # Conversion factors to points
    conversions = {
        'pt': 1.0,
        'pc': 12.0,  # 1 pica = 12 points
        'in': 72.27,  # 1 inch = 72.27 points
        'bp': 1.00375,  # 1 big point = 1.00375 points
        'cm': 28.4527559,  # 1 cm = 28.4527559 points
        'mm': 2.84527559,  # 1 mm = 2.84527559 points
        'dd': 1.07,  # 1 didot point
        'cc': 12.84,  # 1 cicero = 12 didot points
        'sp': 1/65536,  # 1 scaled point
        'ex': 4.3,  # approximate
        'em': 10.0,  # approximate (depends on font)
    }
    if unit in conversions:
        return value * conversions[unit]
    return None


def dim_abs_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \dim_abs:n { -10pt }  ->  10pt
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    parsed = _parse_dim_value(expr_str)
    if parsed:
        value, unit = parsed
        abs_value = abs(value)
        if abs_value == int(abs_value):
            return expander.convert_str_to_tokens(f"{int(abs_value)}{unit}")
        return expander.convert_str_to_tokens(f"{abs_value}{unit}")
    return []


def dim_sign_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \dim_sign:n { -10pt }  ->  -1
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    parsed = _parse_dim_value(expr_str)
    if parsed:
        value, _ = parsed
        if value > 0:
            return expander.convert_str_to_tokens("1")
        elif value < 0:
            return expander.convert_str_to_tokens("-1")
        else:
            return expander.convert_str_to_tokens("0")
    return []


def dim_max_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \dim_max:nn { 10pt } { 20pt }  ->  20pt
    """
    expander.skip_whitespace()
    a_tokens = expander.parse_brace_as_tokens() or []
    a_str = "".join(t.value for t in a_tokens).strip()
    expander.skip_whitespace()
    b_tokens = expander.parse_brace_as_tokens() or []
    b_str = "".join(t.value for t in b_tokens).strip()

    a_parsed = _parse_dim_value(a_str)
    b_parsed = _parse_dim_value(b_str)

    if a_parsed and b_parsed:
        a_pt = _to_pt(a_parsed[0], a_parsed[1])
        b_pt = _to_pt(b_parsed[0], b_parsed[1])
        if a_pt is not None and b_pt is not None:
            if a_pt >= b_pt:
                value, unit = a_parsed
            else:
                value, unit = b_parsed
            if value == int(value):
                return expander.convert_str_to_tokens(f"{int(value)}{unit}")
            return expander.convert_str_to_tokens(f"{value}{unit}")
    return []


def dim_min_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \dim_min:nn { 10pt } { 20pt }  ->  10pt
    """
    expander.skip_whitespace()
    a_tokens = expander.parse_brace_as_tokens() or []
    a_str = "".join(t.value for t in a_tokens).strip()
    expander.skip_whitespace()
    b_tokens = expander.parse_brace_as_tokens() or []
    b_str = "".join(t.value for t in b_tokens).strip()

    a_parsed = _parse_dim_value(a_str)
    b_parsed = _parse_dim_value(b_str)

    if a_parsed and b_parsed:
        a_pt = _to_pt(a_parsed[0], a_parsed[1])
        b_pt = _to_pt(b_parsed[0], b_parsed[1])
        if a_pt is not None and b_pt is not None:
            if a_pt <= b_pt:
                value, unit = a_parsed
            else:
                value, unit = b_parsed
            if value == int(value):
                return expander.convert_str_to_tokens(f"{int(value)}{unit}")
            return expander.convert_str_to_tokens(f"{value}{unit}")
    return []


def dim_to_fp_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \dim_to_fp:n { 10pt }  ->  10.0
    Convert dimension to floating point (in pt).
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    parsed = _parse_dim_value(expr_str)
    if parsed:
        value, unit = parsed
        pt_value = _to_pt(value, unit)
        if pt_value is not None:
            if pt_value == int(pt_value):
                return expander.convert_str_to_tokens(str(int(pt_value)))
            return expander.convert_str_to_tokens(str(pt_value))
    return []


def register_dim_handlers(expander: ExpanderCore) -> None:
    """Register dimension handlers."""
    # Creation
    expander.register_handler("\\dim_new:N", dim_new_handler, is_global=True)

    # Setting
    for name in ["\\dim_set:Nn", "\\dim_set:cn", "\\dim_set:Nx"]:
        expander.register_handler(name, dim_set_handler, is_global=True)
    for name in ["\\dim_gset:Nn", "\\dim_gset:cn"]:
        expander.register_handler(name, dim_gset_handler, is_global=True)

    # Arithmetic
    for name in ["\\dim_add:Nn", "\\dim_gadd:Nn"]:
        expander.register_handler(name, dim_add_handler, is_global=True)
    for name in ["\\dim_sub:Nn", "\\dim_gsub:Nn"]:
        expander.register_handler(name, dim_sub_handler, is_global=True)

    # Zeroing
    for name in ["\\dim_zero:N", "\\dim_gzero:N"]:
        expander.register_handler(name, dim_zero_handler, is_global=True)

    # Using
    for name in ["\\dim_use:N", "\\dim_use:c"]:
        expander.register_handler(name, dim_use_handler, is_global=True)

    # Evaluation
    expander.register_handler("\\dim_eval:n", dim_eval_handler, is_global=True)

    # Comparison
    for name in ["\\dim_compare:nTF", "\\dim_compare:nNnTF"]:
        expander.register_handler(name, dim_compare_TF_handler, is_global=True)
    expander.register_handler("\\dim_compare:nT", dim_compare_T_handler, is_global=True)
    expander.register_handler("\\dim_compare:nF", dim_compare_F_handler, is_global=True)

    # Math functions
    expander.register_handler("\\dim_abs:n", dim_abs_handler, is_global=True)
    expander.register_handler("\\dim_sign:n", dim_sign_handler, is_global=True)
    expander.register_handler("\\dim_max:nn", dim_max_handler, is_global=True)
    expander.register_handler("\\dim_min:nn", dim_min_handler, is_global=True)

    # Conversion
    expander.register_handler("\\dim_to_fp:n", dim_to_fp_handler, is_global=True)
