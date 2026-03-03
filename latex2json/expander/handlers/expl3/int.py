r"""
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


def int_gincr_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_gincr:N \g_my_int  ->  \global\advance\g_my_int 1
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        result = [
            Token(TokenType.CONTROL_SEQUENCE, "global"),
            Token(TokenType.CONTROL_SEQUENCE, "advance"),
            var,
        ]
        result.extend(expander.convert_str_to_tokens("1"))
        expander.push_tokens(result)
    return []


def int_gdecr_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_gdecr:N \g_my_int  ->  \global\advance\g_my_int -1
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        result = [
            Token(TokenType.CONTROL_SEQUENCE, "global"),
            Token(TokenType.CONTROL_SEQUENCE, "advance"),
            var,
        ]
        result.extend(expander.convert_str_to_tokens("-1"))
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


def int_compare_T_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_compare:nT { 1 > 0 } {true}
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    result = _eval_int_compare(expr_str)
    if result:
        expander.push_tokens(true_branch)
    return []


def int_compare_F_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_compare:nF { 1 > 0 } {false}
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    result = _eval_int_compare(expr_str)
    if not result:
        expander.push_tokens(false_branch)
    return []


def int_step_inline_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_step_inline:nn {5} {code with #1}
    Iterates from 1 to n, replacing #1 with current value.

    \int_step_inline:nnnn {start} {step} {end} {code with #1}
    Iterates from start to end with step, replacing #1 with current value.
    """
    expander.skip_whitespace()

    # Check if this is the nnnn variant by counting braced groups
    first_tokens = expander.parse_brace_as_tokens() or []
    first_str = "".join(t.value for t in first_tokens).strip()

    expander.skip_whitespace()
    second_tokens = expander.parse_brace_as_tokens() or []
    second_str = "".join(t.value for t in second_tokens).strip()

    # Try to determine if this is nn or nnnn variant
    # Check if second_tokens looks like code (contains #1)
    has_param = any(t.type == TokenType.PARAMETER for t in second_tokens)

    if has_param:
        # This is \int_step_inline:nn {n} {code}
        try:
            end = int(first_str)
        except ValueError:
            return []

        body = second_tokens
        start = 1
        step = 1
    else:
        # This is \int_step_inline:nnnn {start} {step} {end} {code}
        expander.skip_whitespace()
        third_tokens = expander.parse_brace_as_tokens() or []
        third_str = "".join(t.value for t in third_tokens).strip()

        expander.skip_whitespace()
        body = expander.parse_brace_as_tokens() or []

        try:
            start = int(first_str)
            step = int(second_str)
            end = int(third_str)
        except ValueError:
            return []

    # Build result: for each value, substitute #1 in body
    result_tokens = []
    current = start
    if step > 0:
        while current <= end:
            for tok in body:
                if tok.type == TokenType.PARAMETER and tok.value == "1":
                    result_tokens.extend(expander.convert_str_to_tokens(str(current)))
                else:
                    result_tokens.append(tok)
            current += step
    elif step < 0:
        while current >= end:
            for tok in body:
                if tok.type == TokenType.PARAMETER and tok.value == "1":
                    result_tokens.extend(expander.convert_str_to_tokens(str(current)))
                else:
                    result_tokens.append(tok)
            current += step

    expander.push_tokens(result_tokens)
    return []


def int_step_function_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_step_function:nN {5} \func
    Calls \func{1}\func{2}...\func{5}

    \int_step_function:nnnN {start} {step} {end} \func
    """
    expander.skip_whitespace()

    first_tokens = expander.parse_brace_as_tokens() or []
    first_str = "".join(t.value for t in first_tokens).strip()

    expander.skip_whitespace()

    # Check if next is a control sequence or another brace group
    next_tok = expander.peek()
    if next_tok and next_tok.type == TokenType.CONTROL_SEQUENCE:
        # This is \int_step_function:nN {n} \func
        func = expander.consume()
        try:
            end = int(first_str)
        except ValueError:
            return []
        start = 1
        step = 1
    else:
        # This is \int_step_function:nnnN {start} {step} {end} \func
        second_tokens = expander.parse_brace_as_tokens() or []
        second_str = "".join(t.value for t in second_tokens).strip()

        expander.skip_whitespace()
        third_tokens = expander.parse_brace_as_tokens() or []
        third_str = "".join(t.value for t in third_tokens).strip()

        expander.skip_whitespace()
        func = expander.consume()

        try:
            start = int(first_str)
            step = int(second_str)
            end = int(third_str)
        except ValueError:
            return []

    if not func:
        return []

    # Build result: \func{1}\func{2}...
    result_tokens = []
    current = start
    if step > 0:
        while current <= end:
            result_tokens.append(func)
            result_tokens.append(Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP))
            result_tokens.extend(expander.convert_str_to_tokens(str(current)))
            result_tokens.append(Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP))
            current += step
    elif step < 0:
        while current >= end:
            result_tokens.append(func)
            result_tokens.append(Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP))
            result_tokens.extend(expander.convert_str_to_tokens(str(current)))
            result_tokens.append(Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP))
            current += step

    expander.push_tokens(result_tokens)
    return []


def int_do_while_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_do_while:nNnn {value1} <relation> {value2} {code}
    Execute code while relation is true.

    Note: We limit iterations to prevent infinite loops.
    """
    expander.skip_whitespace()
    val1_tokens = expander.parse_brace_as_tokens() or []
    val1_str = "".join(t.value for t in val1_tokens).strip()

    expander.skip_whitespace()
    relation = expander.consume()
    if not relation:
        return []
    rel_str = relation.value

    expander.skip_whitespace()
    val2_tokens = expander.parse_brace_as_tokens() or []
    val2_str = "".join(t.value for t in val2_tokens).strip()

    expander.skip_whitespace()
    body = expander.parse_brace_as_tokens() or []

    # Build comparison expression
    expr_str = f"{val1_str} {rel_str} {val2_str}"

    result_tokens = []
    max_iterations = 1000  # Safety limit
    iterations = 0

    while _eval_int_compare(expr_str) and iterations < max_iterations:
        result_tokens.extend(body[:])
        iterations += 1

    expander.push_tokens(result_tokens)
    return []


def int_do_until_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_do_until:nNnn {value1} <relation> {value2} {code}
    Execute code until relation becomes true.

    Note: We limit iterations to prevent infinite loops.
    """
    expander.skip_whitespace()
    val1_tokens = expander.parse_brace_as_tokens() or []
    val1_str = "".join(t.value for t in val1_tokens).strip()

    expander.skip_whitespace()
    relation = expander.consume()
    if not relation:
        return []
    rel_str = relation.value

    expander.skip_whitespace()
    val2_tokens = expander.parse_brace_as_tokens() or []
    val2_str = "".join(t.value for t in val2_tokens).strip()

    expander.skip_whitespace()
    body = expander.parse_brace_as_tokens() or []

    # Build comparison expression
    expr_str = f"{val1_str} {rel_str} {val2_str}"

    result_tokens = []
    max_iterations = 1000  # Safety limit
    iterations = 0

    while not _eval_int_compare(expr_str) and iterations < max_iterations:
        result_tokens.extend(body[:])
        iterations += 1

    expander.push_tokens(result_tokens)
    return []


def int_while_do_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_while_do:nNnn {value1} <relation> {value2} {code}
    While relation is true, execute code (checks condition first).
    """
    return int_do_while_handler(expander, _token)


def int_until_do_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_until_do:nNnn {value1} <relation> {value2} {code}
    Until relation becomes true, execute code (checks condition first).
    """
    return int_do_until_handler(expander, _token)


def int_case_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_case:nn {value} { {1}{result1} {2}{result2} }
    or
    \int_case:nnTF {value} { {1}{result1} {2}{result2} } {true} {false}
    """
    expander.skip_whitespace()
    value_tokens = expander.parse_brace_as_tokens() or []
    value_str = "".join(t.value for t in value_tokens).strip()

    try:
        value = int(value_str)
    except ValueError:
        return []

    expander.skip_whitespace()
    cases_tokens = expander.parse_brace_as_tokens() or []

    # Parse cases: {key}{value}{key}{value}...
    cases = _parse_case_pairs(cases_tokens)

    # Find matching case
    for case_val, result in cases:
        try:
            if int(case_val) == value:
                expander.push_tokens(result)
                return []
        except ValueError:
            continue

    return []


def _parse_case_pairs(tokens: List[Token]) -> List[tuple]:
    """Parse {key}{value}{key}{value}... into list of (key_str, value_tokens)."""
    pairs = []
    i = 0

    while i < len(tokens):
        # Skip whitespace
        while i < len(tokens) and tokens[i].value.isspace():
            i += 1

        if i >= len(tokens):
            break

        tok = tokens[i]
        if tok.catcode == Catcode.BEGIN_GROUP or (
            tok.type == TokenType.CHARACTER and tok.value == "{"
        ):
            # Parse key
            depth = 1
            key_tokens = []
            i += 1
            while i < len(tokens) and depth > 0:
                t = tokens[i]
                if t.catcode == Catcode.BEGIN_GROUP or (
                    t.type == TokenType.CHARACTER and t.value == "{"
                ):
                    depth += 1
                    key_tokens.append(t)
                elif t.catcode == Catcode.END_GROUP or (
                    t.type == TokenType.CHARACTER and t.value == "}"
                ):
                    depth -= 1
                    if depth > 0:
                        key_tokens.append(t)
                else:
                    key_tokens.append(t)
                i += 1

            # Skip whitespace
            while i < len(tokens) and tokens[i].value.isspace():
                i += 1

            if i >= len(tokens):
                break

            # Parse value
            tok = tokens[i]
            if tok.catcode == Catcode.BEGIN_GROUP or (
                tok.type == TokenType.CHARACTER and tok.value == "{"
            ):
                depth = 1
                value_tokens = []
                i += 1
                while i < len(tokens) and depth > 0:
                    t = tokens[i]
                    if t.catcode == Catcode.BEGIN_GROUP or (
                        t.type == TokenType.CHARACTER and t.value == "{"
                    ):
                        depth += 1
                        value_tokens.append(t)
                    elif t.catcode == Catcode.END_GROUP or (
                        t.type == TokenType.CHARACTER and t.value == "}"
                    ):
                        depth -= 1
                        if depth > 0:
                            value_tokens.append(t)
                    else:
                        value_tokens.append(t)
                    i += 1

                key_str = "".join(t.value for t in key_tokens).strip()
                pairs.append((key_str, value_tokens))
        else:
            i += 1

    return pairs


def int_abs_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_abs:n { -5 }  ->  5
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    result = _safe_eval_int(expr_str)
    if result is not None:
        return expander.convert_str_to_tokens(str(abs(result)))
    return []


def int_sign_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_sign:n { -5 }  ->  -1
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    result = _safe_eval_int(expr_str)
    if result is not None:
        if result > 0:
            return expander.convert_str_to_tokens("1")
        elif result < 0:
            return expander.convert_str_to_tokens("-1")
        else:
            return expander.convert_str_to_tokens("0")
    return []


def int_max_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_max:nn { 3 } { 5 }  ->  5
    """
    expander.skip_whitespace()
    a_tokens = expander.parse_brace_as_tokens() or []
    a_str = "".join(t.value for t in a_tokens).strip()
    expander.skip_whitespace()
    b_tokens = expander.parse_brace_as_tokens() or []
    b_str = "".join(t.value for t in b_tokens).strip()

    a = _safe_eval_int(a_str)
    b = _safe_eval_int(b_str)
    if a is not None and b is not None:
        return expander.convert_str_to_tokens(str(max(a, b)))
    return []


def int_min_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_min:nn { 3 } { 5 }  ->  3
    """
    expander.skip_whitespace()
    a_tokens = expander.parse_brace_as_tokens() or []
    a_str = "".join(t.value for t in a_tokens).strip()
    expander.skip_whitespace()
    b_tokens = expander.parse_brace_as_tokens() or []
    b_str = "".join(t.value for t in b_tokens).strip()

    a = _safe_eval_int(a_str)
    b = _safe_eval_int(b_str)
    if a is not None and b is not None:
        return expander.convert_str_to_tokens(str(min(a, b)))
    return []


def int_mod_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_mod:nn { 10 } { 3 }  ->  1
    """
    expander.skip_whitespace()
    a_tokens = expander.parse_brace_as_tokens() or []
    a_str = "".join(t.value for t in a_tokens).strip()
    expander.skip_whitespace()
    b_tokens = expander.parse_brace_as_tokens() or []
    b_str = "".join(t.value for t in b_tokens).strip()

    a = _safe_eval_int(a_str)
    b = _safe_eval_int(b_str)
    if a is not None and b is not None and b != 0:
        return expander.convert_str_to_tokens(str(a % b))
    return []


def int_div_truncate_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \int_div_truncate:nn { 10 } { 3 }  ->  3
    """
    expander.skip_whitespace()
    a_tokens = expander.parse_brace_as_tokens() or []
    a_str = "".join(t.value for t in a_tokens).strip()
    expander.skip_whitespace()
    b_tokens = expander.parse_brace_as_tokens() or []
    b_str = "".join(t.value for t in b_tokens).strip()

    a = _safe_eval_int(a_str)
    b = _safe_eval_int(b_str)
    if a is not None and b is not None and b != 0:
        return expander.convert_str_to_tokens(str(int(a / b)))
    return []


def int_if_odd_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_if_odd:nTF { 3 } {true} {false}
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    result = _safe_eval_int(expr_str)
    if result is not None and result % 2 != 0:
        expander.push_tokens(true_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def int_if_even_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_if_even:nTF { 4 } {true} {false}
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    result = _safe_eval_int(expr_str)
    if result is not None and result % 2 == 0:
        expander.push_tokens(true_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def int_to_alph_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_to_alph:n { 1 }  ->  a
    \int_to_alph:n { 26 } ->  z
    \int_to_alph:n { 27 } ->  aa
    Converts integer to lowercase alphabetic representation.
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    result = _safe_eval_int(expr_str)
    if result is not None and result > 0:
        # Convert to alphabetic (a=1, b=2, ..., z=26, aa=27, ...)
        alpha = ""
        n = result
        while n > 0:
            n -= 1
            alpha = chr(ord('a') + (n % 26)) + alpha
            n //= 26
        return expander.convert_str_to_tokens(alpha)
    return []


def int_to_Alph_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_to_Alph:n { 1 }  ->  A
    Converts integer to uppercase alphabetic representation.
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    result = _safe_eval_int(expr_str)
    if result is not None and result > 0:
        alpha = ""
        n = result
        while n > 0:
            n -= 1
            alpha = chr(ord('A') + (n % 26)) + alpha
            n //= 26
        return expander.convert_str_to_tokens(alpha)
    return []


def int_to_roman_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_to_roman:n { 4 }  ->  iv
    Converts integer to lowercase roman numerals.
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    result = _safe_eval_int(expr_str)
    if result is not None and result > 0:
        roman = _int_to_roman(result)
        return expander.convert_str_to_tokens(roman.lower())
    return []


def int_to_Roman_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_to_Roman:n { 4 }  ->  IV
    Converts integer to uppercase roman numerals.
    """
    expander.skip_whitespace()
    expr_tokens = expander.parse_brace_as_tokens() or []
    expr_str = "".join(t.value for t in expr_tokens).strip()

    result = _safe_eval_int(expr_str)
    if result is not None and result > 0:
        roman = _int_to_roman(result)
        return expander.convert_str_to_tokens(roman)
    return []


def _int_to_roman(num: int) -> str:
    """Convert integer to Roman numerals."""
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syms[i]
            num -= val[i]
        i += 1
    return roman_num


def int_compare_p_nNn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \int_compare_p:nNn {expr1} <relation> {expr2}

    Predicate form — consumes arguments. Used inside boolean expressions
    but we cannot produce a result that expl3 boolean parsing can evaluate.
    Returns empty.
    """
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # expr1

    expander.skip_whitespace()
    expander.consume()  # relation token (=, <, >)

    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # expr2

    return []


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
    expander.register_handler("\\int_gincr:N", int_gincr_handler, is_global=True)
    expander.register_handler("\\int_decr:N", int_decr_handler, is_global=True)
    expander.register_handler("\\int_gdecr:N", int_gdecr_handler, is_global=True)

    # Zeroing
    for name in ["\\int_zero:N", "\\int_gzero:N"]:
        expander.register_handler(name, int_zero_handler, is_global=True)

    # Using
    for name in ["\\int_use:N", "\\int_use:c"]:
        expander.register_handler(name, int_use_handler, is_global=True)

    # Comparison
    for name in ["\\int_compare:nTF", "\\int_compare:nNnTF"]:
        expander.register_handler(name, int_compare_TF_handler, is_global=True)
    expander.register_handler("\\int_compare:nT", int_compare_T_handler, is_global=True)
    expander.register_handler("\\int_compare:nF", int_compare_F_handler, is_global=True)

    # Evaluation
    expander.register_handler("\\int_eval:n", int_eval_handler, is_global=True)

    # Stepping/looping
    for name in ["\\int_step_inline:nn", "\\int_step_inline:nnnn"]:
        expander.register_handler(name, int_step_inline_handler, is_global=True)
    for name in ["\\int_step_function:nN", "\\int_step_function:nnnN"]:
        expander.register_handler(name, int_step_function_handler, is_global=True)

    # While/until loops
    expander.register_handler("\\int_do_while:nNnn", int_do_while_handler, is_global=True)
    expander.register_handler("\\int_do_until:nNnn", int_do_until_handler, is_global=True)
    expander.register_handler("\\int_while_do:nNnn", int_while_do_handler, is_global=True)
    expander.register_handler("\\int_until_do:nNnn", int_until_do_handler, is_global=True)

    # Case
    for name in ["\\int_case:nn", "\\int_case:nnTF"]:
        expander.register_handler(name, int_case_handler, is_global=True)

    # Math functions
    expander.register_handler("\\int_abs:n", int_abs_handler, is_global=True)
    expander.register_handler("\\int_sign:n", int_sign_handler, is_global=True)
    expander.register_handler("\\int_max:nn", int_max_handler, is_global=True)
    expander.register_handler("\\int_min:nn", int_min_handler, is_global=True)
    expander.register_handler("\\int_mod:nn", int_mod_handler, is_global=True)
    expander.register_handler("\\int_div_truncate:nn", int_div_truncate_handler, is_global=True)

    # Odd/even
    expander.register_handler("\\int_if_odd:nTF", int_if_odd_TF_handler, is_global=True)
    expander.register_handler("\\int_if_even:nTF", int_if_even_TF_handler, is_global=True)

    # Conversion to text representations
    expander.register_handler("\\int_to_alph:n", int_to_alph_handler, is_global=True)
    expander.register_handler("\\int_to_Alph:n", int_to_Alph_handler, is_global=True)
    expander.register_handler("\\int_to_roman:n", int_to_roman_handler, is_global=True)
    expander.register_handler("\\int_to_Roman:n", int_to_Roman_handler, is_global=True)

    # Predicate form (used inside boolean expressions)
    expander.register_handler(
        "\\int_compare_p:nNn", int_compare_p_nNn_handler, is_global=True
    )
