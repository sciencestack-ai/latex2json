"""
expl3 floating point (fp) handlers.

Handles \fp_new:N, \fp_set:Nn, \fp_eval:n, \fp_compare:nTF,
and related functions.

Floating point numbers are stored in a dedicated dictionary since TeX has no
native floating point register type. This is similar to how expl3 implements
fp internally.
"""

import math
import re
from typing import Dict, List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


# Dedicated storage for floating point values: {var_name: float_value}
# This is necessary because TeX has no native fp register type.
_fp_store: Dict[str, float] = {}


def _get_var_name(var: Token) -> str:
    """Get the variable name from a token."""
    return var.value


def _get_fp(name: str) -> float:
    """Get fp value from store, defaulting to 0.0."""
    return _fp_store.get(name, 0.0)


def _set_fp(name: str, value: float) -> None:
    """Set fp value in store."""
    _fp_store[name] = value


def fp_new_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \fp_new:N \l_my_fp
    Create a new fp variable initialized to 0.
    """
    expander.skip_whitespace()
    var = expander.consume()
    if var:
        name = _get_var_name(var)
        _set_fp(name, 0.0)
    return []


def fp_zero_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \fp_zero:N \l_my_fp
    Set an fp variable to 0.
    """
    expander.skip_whitespace()
    var = expander.consume()
    if var:
        name = _get_var_name(var)
        _set_fp(name, 0.0)
    return []


def fp_set_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \fp_set:Nn \l_my_fp {3.14}
    Set an fp variable to a value (with expression evaluation).
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    value_tokens = expander.parse_brace_as_tokens() or []
    value_str = "".join(t.value for t in value_tokens).strip()

    if var:
        name = _get_var_name(var)
        result = _safe_eval_fp(value_str)
        if result is not None:
            _set_fp(name, result)
    return []


def fp_gset_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \fp_gset:Nn \g_my_fp {3.14}
    Globally set an fp variable to a value.
    Note: In our implementation, all fp storage is global by nature.
    """
    # Same as fp_set since our store is global
    return fp_set_handler(expander, _token)


def fp_add_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \fp_add:Nn \l_my_fp {1.5}
    Add a value to an fp variable.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    value_tokens = expander.parse_brace_as_tokens() or []
    value_str = "".join(t.value for t in value_tokens).strip()

    if var:
        name = _get_var_name(var)
        current = _get_fp(name)
        add_val = _safe_eval_fp(value_str)
        if add_val is not None:
            _set_fp(name, current + add_val)
    return []


def fp_sub_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \fp_sub:Nn \l_my_fp {1.5}
    Subtract a value from an fp variable.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    value_tokens = expander.parse_brace_as_tokens() or []
    value_str = "".join(t.value for t in value_tokens).strip()

    if var:
        name = _get_var_name(var)
        current = _get_fp(name)
        sub_val = _safe_eval_fp(value_str)
        if sub_val is not None:
            _set_fp(name, current - sub_val)
    return []


def fp_use_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \fp_use:N \l_my_fp
    Output the value of an fp variable.
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        name = _get_var_name(var)
        value = _get_fp(name)
        return expander.convert_str_to_tokens(_format_fp(value))
    return []


def fp_eval_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \fp_eval:n { 1.5 + 2.5 * 3 }  ->  9.0
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    result = _safe_eval_fp(expr_str)
    if result is not None:
        return expander.convert_str_to_tokens(_format_fp(result))
    return []


def fp_compare_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \fp_compare:nTF { 1.5 > 1.0 } {true} {false}

    Supports: <, >, =, <=, >=, !=
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    result = _eval_fp_compare(expr_str)
    if result:
        expander.push_tokens(true_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def fp_compare_T_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \fp_compare:nT { 1.5 > 1.0 } {true}
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    result = _eval_fp_compare(expr_str)
    if result:
        expander.push_tokens(true_branch)
    return []


def fp_compare_F_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \fp_compare:nF { 1.5 > 1.0 } {false}
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    result = _eval_fp_compare(expr_str)
    if not result:
        expander.push_tokens(false_branch)
    return []


def _eval_fp_compare(expr_str: str) -> bool:
    """Evaluate floating point comparison expression."""
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
        ("=", lambda a, b: abs(a - b) < 1e-10),
    ]:
        if op in expr_str:
            parts = expr_str.split(op, 1)
            if len(parts) == 2:
                try:
                    left = _safe_eval_fp(parts[0].strip())
                    right = _safe_eval_fp(parts[1].strip())
                    if left is not None and right is not None:
                        return func(left, right)
                except (ValueError, TypeError):
                    continue
    return False


def fp_to_int_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \fp_to_int:n { 3.7 }  ->  4 (rounded)
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    result = _safe_eval_fp(expr_str)
    if result is not None:
        return expander.convert_str_to_tokens(str(round(result)))
    return []


def fp_abs_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \fp_abs:n { -3.5 }  ->  3.5
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    result = _safe_eval_fp(expr_str)
    if result is not None:
        return expander.convert_str_to_tokens(_format_fp(abs(result)))
    return []


def fp_sign_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \fp_sign:n { -3.5 }  ->  -1
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    result = _safe_eval_fp(expr_str)
    if result is not None:
        if result > 0:
            return expander.convert_str_to_tokens("1")
        elif result < 0:
            return expander.convert_str_to_tokens("-1")
        else:
            return expander.convert_str_to_tokens("0")
    return []


def fp_max_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \fp_max:nn { 1.5 } { 2.5 }  ->  2.5
    """
    expander.skip_whitespace()
    a_tokens = expander.parse_brace_as_tokens() or []
    a_str = "".join(t.value for t in a_tokens).strip()
    expander.skip_whitespace()
    b_tokens = expander.parse_brace_as_tokens() or []
    b_str = "".join(t.value for t in b_tokens).strip()

    a = _safe_eval_fp(a_str)
    b = _safe_eval_fp(b_str)
    if a is not None and b is not None:
        return expander.convert_str_to_tokens(_format_fp(max(a, b)))
    return []


def fp_min_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \fp_min:nn { 1.5 } { 2.5 }  ->  1.5
    """
    expander.skip_whitespace()
    a_tokens = expander.parse_brace_as_tokens() or []
    a_str = "".join(t.value for t in a_tokens).strip()
    expander.skip_whitespace()
    b_tokens = expander.parse_brace_as_tokens() or []
    b_str = "".join(t.value for t in b_tokens).strip()

    a = _safe_eval_fp(a_str)
    b = _safe_eval_fp(b_str)
    if a is not None and b is not None:
        return expander.convert_str_to_tokens(_format_fp(min(a, b)))
    return []


def _safe_eval_fp(expr_str: str) -> Optional[float]:
    """Safely evaluate floating point arithmetic expression."""
    # Replace expl3 functions with Python equivalents
    expr_str = expr_str.replace("^", "**")

    # Handle common math functions
    func_map = {
        "sin": "math.sin",
        "cos": "math.cos",
        "tan": "math.tan",
        "exp": "math.exp",
        "ln": "math.log",
        "sqrt": "math.sqrt",
        "abs": "abs",
        "round": "round",
        "floor": "math.floor",
        "ceil": "math.ceil",
    }

    for func, replacement in func_map.items():
        expr_str = re.sub(rf"\b{func}\s*\(", f"{replacement}(", expr_str)

    # Handle pi and e
    expr_str = re.sub(r"\bpi\b", str(math.pi), expr_str)
    expr_str = re.sub(r"\be\b", str(math.e), expr_str)

    # Only allow safe characters
    if not re.match(r"^[\d\s.+\-*/()e,mathsincoqlgrufbEpi]+$", expr_str):
        # Try simple number
        try:
            return float(expr_str)
        except ValueError:
            return None

    try:
        result = eval(expr_str, {"__builtins__": {}, "math": math, "abs": abs, "round": round})
        return float(result)
    except Exception:
        try:
            return float(expr_str)
        except ValueError:
            return None


def _format_fp(value: float) -> str:
    """Format floating point number, removing trailing zeros."""
    if value == int(value):
        return str(int(value))
    result = f"{value:.10f}".rstrip("0").rstrip(".")
    return result


def register_fp_handlers(expander: ExpanderCore) -> None:
    """Register floating point handlers."""
    # Creation
    for name in ["\\fp_new:N", "\\fp_new:c"]:
        expander.register_handler(name, fp_new_handler, is_global=True)

    # Zeroing
    for name in ["\\fp_zero:N", "\\fp_gzero:N"]:
        expander.register_handler(name, fp_zero_handler, is_global=True)

    # Setting
    for name in ["\\fp_set:Nn", "\\fp_set:cn", "\\fp_set:Nx"]:
        expander.register_handler(name, fp_set_handler, is_global=True)
    for name in ["\\fp_gset:Nn", "\\fp_gset:cn"]:
        expander.register_handler(name, fp_gset_handler, is_global=True)

    # Arithmetic
    for name in ["\\fp_add:Nn", "\\fp_gadd:Nn"]:
        expander.register_handler(name, fp_add_handler, is_global=True)
    for name in ["\\fp_sub:Nn", "\\fp_gsub:Nn"]:
        expander.register_handler(name, fp_sub_handler, is_global=True)

    # Using
    for name in ["\\fp_use:N", "\\fp_use:c"]:
        expander.register_handler(name, fp_use_handler, is_global=True)

    # Evaluation
    expander.register_handler("\\fp_eval:n", fp_eval_handler, is_global=True)

    # Comparison
    expander.register_handler("\\fp_compare:nTF", fp_compare_TF_handler, is_global=True)
    expander.register_handler("\\fp_compare:nT", fp_compare_T_handler, is_global=True)
    expander.register_handler("\\fp_compare:nF", fp_compare_F_handler, is_global=True)

    # Conversion
    expander.register_handler("\\fp_to_int:n", fp_to_int_handler, is_global=True)

    # Math functions
    expander.register_handler("\\fp_abs:n", fp_abs_handler, is_global=True)
    expander.register_handler("\\fp_sign:n", fp_sign_handler, is_global=True)
    expander.register_handler("\\fp_max:nn", fp_max_handler, is_global=True)
    expander.register_handler("\\fp_min:nn", fp_min_handler, is_global=True)
