"""
expl3 integer (int) handlers.

Handles \int_new:N, \int_set:Nn, \int_add:Nn, \int_incr:N, \int_decr:N,
\int_use:N, \int_compare:nTF, \int_eval:n, etc.
"""

import re
from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType


def int_new_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_new:N \l_my_int  ->  \newcount\l_my_int
    """
    expander.skip_whitespace()
    var = expander.consume()
    if var:
        expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "newcount"), var])
    return []


def int_set_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_set:Nn \l_my_int {5}  ->  \l_my_int=5
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    value_tokens = expander.parse_brace_as_tokens() or []
    value_str = "".join(t.value for t in value_tokens).strip()

    if var:
        result = [var, Token(TokenType.CHARACTER, "=", catcode=Catcode.OTHER)]
        result.extend(expander.convert_str_to_tokens(value_str))
        expander.push_tokens(result)
    return []


def int_gset_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_gset:Nn \g_my_int {5}  ->  \global\g_my_int=5
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    value_tokens = expander.parse_brace_as_tokens() or []
    value_str = "".join(t.value for t in value_tokens).strip()

    if var:
        result = [
            Token(TokenType.CONTROL_SEQUENCE, "global"),
            var,
            Token(TokenType.CHARACTER, "=", catcode=Catcode.OTHER),
        ]
        result.extend(expander.convert_str_to_tokens(value_str))
        expander.push_tokens(result)
    return []


def int_add_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_add:Nn \l_my_int {5}  ->  \advance\l_my_int 5
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    value_tokens = expander.parse_brace_as_tokens() or []
    value_str = "".join(t.value for t in value_tokens).strip()

    if var:
        result = [Token(TokenType.CONTROL_SEQUENCE, "advance"), var]
        result.extend(expander.convert_str_to_tokens(value_str))
        expander.push_tokens(result)
    return []


def int_incr_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_incr:N \l_my_int  ->  \advance\l_my_int 1
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        result = [Token(TokenType.CONTROL_SEQUENCE, "advance"), var]
        result.extend(expander.convert_str_to_tokens("1"))
        expander.push_tokens(result)
    return []


def int_decr_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_decr:N \l_my_int  ->  \advance\l_my_int -1
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        result = [Token(TokenType.CONTROL_SEQUENCE, "advance"), var]
        result.extend(expander.convert_str_to_tokens("-1"))
        expander.push_tokens(result)
    return []


def int_zero_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_zero:N \l_my_int  ->  \l_my_int=0
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        expander.push_tokens(
            [
                var,
                Token(TokenType.CHARACTER, "=", catcode=Catcode.OTHER),
                Token(TokenType.CHARACTER, "0", catcode=Catcode.OTHER),
            ]
        )
    return []


def int_use_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_use:N \l_my_int  ->  \the\l_my_int
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "the"), var])
    return []


def int_compare_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_compare:nTF { 1 > 0 } {true} {false}

    Supports: <, >, =, <=, >=, !=
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    result = _eval_int_compare(expr_str)
    if result:
        expander.push_tokens(true_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def _eval_int_compare(expr_str: str) -> bool:
    """Evaluate integer comparison expression."""
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
        ("=", lambda a, b: a == b),
    ]:
        if op in expr_str:
            parts = expr_str.split(op, 1)
            if len(parts) == 2:
                try:
                    left = int(parts[0].strip())
                    right = int(parts[1].strip())
                    return func(left, right)
                except ValueError:
                    continue
    return False


def int_eval_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_eval:n { 1 + 2 * 3 }  ->  7
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    try:
        result = _safe_eval_int(expr_str)
        if result is not None:
            return expander.convert_str_to_tokens(str(result))
    except Exception:
        pass
    return []


def _safe_eval_int(expr_str: str) -> Optional[int]:
    """Safely evaluate integer arithmetic expression."""
    # Only allow digits, operators, parentheses, spaces
    if not re.match(r"^[\d\s+\-*/()]+$", expr_str):
        return None
    try:
        result = eval(expr_str)
        return int(result)
    except Exception:
        return None


def register_int_handlers(expander: ExpanderCore) -> None:
    """Register integer handlers."""
    # Creation
    expander.register_handler("\\int_new:N", int_new_handler, is_global=True)

    # Setting
    for name in ["\\int_set:Nn", "\\int_set:cn"]:
        expander.register_handler(name, int_set_handler, is_global=True)
    for name in ["\\int_gset:Nn", "\\int_gset:cn"]:
        expander.register_handler(name, int_gset_handler, is_global=True)

    # Arithmetic
    for name in ["\\int_add:Nn", "\\int_add:cn"]:
        expander.register_handler(name, int_add_handler, is_global=True)
    expander.register_handler("\\int_incr:N", int_incr_handler, is_global=True)
    expander.register_handler("\\int_decr:N", int_decr_handler, is_global=True)

    # Zeroing
    for name in ["\\int_zero:N", "\\int_gzero:N"]:
        expander.register_handler(name, int_zero_handler, is_global=True)

    # Using
    for name in ["\\int_use:N", "\\int_use:c"]:
        expander.register_handler(name, int_use_handler, is_global=True)

    # Comparison
    for name in ["\\int_compare:nTF", "\\int_compare:nNnTF"]:
        expander.register_handler(name, int_compare_TF_handler, is_global=True)

    # Evaluation
    expander.register_handler("\\int_eval:n", int_eval_handler, is_global=True)
