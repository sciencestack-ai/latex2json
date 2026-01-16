"""
expl3 token list (tl) handlers.

Handles \tl_new:N, \tl_set:Nn, \tl_gset:Nn, \tl_use:N, \tl_put_right:Nn,
\tl_put_left:Nn, \tl_clear:N, \tl_if_empty:nTF, \tl_if_eq:nnTF, etc.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import wrap_tokens_in_braces


def tl_new_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \tl_new:N \l_my_tl  ->  \def\l_my_tl{}
    """
    expander.skip_whitespace()
    var = expander.consume()
    if var:
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
                Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
                Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
            ]
        )
    return []


def tl_set_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \tl_set:Nn \l_my_tl {value}  ->  \def\l_my_tl{value}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    value = expander.parse_brace_as_tokens() or []

    if var:
        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
            + wrap_tokens_in_braces(value)
        )
    return []


def tl_gset_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \tl_gset:Nn \l_my_tl {value}  ->  \global\def\l_my_tl{value}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    value = expander.parse_brace_as_tokens() or []

    if var:
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "global"),
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
            ]
            + wrap_tokens_in_braces(value)
        )
    return []


def tl_use_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \tl_use:N \l_my_tl  ->  expand the variable
    """
    expander.skip_whitespace()
    var = expander.consume()
    if var:
        # Just push the token back - expander will expand it
        expander.push_tokens([var])
    return []


def tl_put_right_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tl_put_right:Nn \l_my_tl {more}  ->  append to existing definition
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    addition = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        existing = macro.definition if macro and macro.definition else []
        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
            + wrap_tokens_in_braces(existing + addition)
        )
    return []


def tl_put_left_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tl_put_left:Nn \l_my_tl {more}  ->  prepend to existing definition
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    addition = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        existing = macro.definition if macro and macro.definition else []
        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
            + wrap_tokens_in_braces(addition + existing)
        )
    return []


def tl_clear_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \tl_clear:N \l_my_tl  ->  \def\l_my_tl{}
    """
    expander.skip_whitespace()
    var = expander.consume()
    if var:
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
                Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
                Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
            ]
        )
    return []


def tl_to_str_n_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tl_to_str:n {tokens}  ->  string representation (detokenize)
    """
    expander.skip_whitespace()
    tokens = expander.parse_brace_as_tokens() or []
    result_str = "".join(t.value for t in tokens)
    return expander.convert_str_to_tokens(result_str)


def tl_to_str_N_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tl_to_str:N \l_my_tl  ->  string representation of variable content
    """
    expander.skip_whitespace()
    var = expander.consume()
    if var:
        macro = expander.get_macro(var)
        if macro and macro.definition:
            result_str = "".join(t.value for t in macro.definition)
            return expander.convert_str_to_tokens(result_str)
    return []


def tl_if_empty_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tl_if_empty:nTF {test} {empty} {not empty}
    """
    expander.skip_whitespace()
    test_tokens = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    # Check if empty (ignoring whitespace)
    is_empty = all(t.value.isspace() for t in test_tokens) if test_tokens else True

    if is_empty:
        expander.push_tokens(true_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def tl_if_empty_T_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tl_if_empty:nT {test} {empty}
    """
    expander.skip_whitespace()
    test_tokens = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    is_empty = all(t.value.isspace() for t in test_tokens) if test_tokens else True

    if is_empty:
        expander.push_tokens(true_branch)
    return []


def tl_if_empty_F_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tl_if_empty:nF {test} {not empty}
    """
    expander.skip_whitespace()
    test_tokens = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    is_empty = all(t.value.isspace() for t in test_tokens) if test_tokens else True

    if not is_empty:
        expander.push_tokens(false_branch)
    return []


def tl_if_eq_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tl_if_eq:nnTF {tl1} {tl2} {true} {false}
    """
    expander.skip_whitespace()
    tl1_tokens = expander.parse_brace_as_tokens() or []
    tl1_str = "".join(t.value for t in tl1_tokens)

    expander.skip_whitespace()
    tl2_tokens = expander.parse_brace_as_tokens() or []
    tl2_str = "".join(t.value for t in tl2_tokens)

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if tl1_str == tl2_str:
        expander.push_tokens(true_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def tl_head_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \tl_head:n {tokens}  ->  first token
    """
    expander.skip_whitespace()
    tokens = expander.parse_brace_as_tokens() or []
    if tokens:
        return [tokens[0]]
    return []


def tl_tail_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \tl_tail:n {tokens}  ->  all but first token
    """
    expander.skip_whitespace()
    tokens = expander.parse_brace_as_tokens() or []
    if len(tokens) > 1:
        return tokens[1:]
    return []


def tl_range_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \tl_range:nnn {token-list} {start} {end}  ->  tokens from start to end

    Extracts a range of tokens from the token list.
    - 1-based indexing (first token is 1)
    - Negative indices count from end (-1 is last token)
    - If start > end (after normalization), returns empty

    Examples:
    - \tl_range:nnn {abcde} {1} {1}  -> a
    - \tl_range:nnn {abcde} {2} {4}  -> bcd
    - \tl_range:nnn {abcde} {2} {-1} -> bcde
    - \tl_range:nnn {abcde} {-2} {-1} -> de
    """
    expander.skip_whitespace()
    tokens = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    start_tokens = expander.parse_brace_as_tokens() or []
    start_str = "".join(t.value for t in start_tokens).strip()

    expander.skip_whitespace()
    end_tokens = expander.parse_brace_as_tokens() or []
    end_str = "".join(t.value for t in end_tokens).strip()

    try:
        start_idx = int(start_str)
        end_idx = int(end_str)
    except ValueError:
        return []

    if not tokens:
        return []

    n = len(tokens)

    # Convert to 0-based indices
    # Positive: 1 -> 0, 2 -> 1, etc.
    # Negative: -1 -> n-1, -2 -> n-2, etc.
    if start_idx > 0:
        start_idx = start_idx - 1
    elif start_idx < 0:
        start_idx = n + start_idx
    else:
        start_idx = 0  # 0 treated as 1

    if end_idx > 0:
        end_idx = end_idx  # end is inclusive, so keep as-is for slicing
    elif end_idx < 0:
        end_idx = n + end_idx + 1  # -1 means last, which is n for slicing
    else:
        end_idx = n  # 0 treated as end

    # Clamp to valid range
    start_idx = max(0, min(start_idx, n))
    end_idx = max(0, min(end_idx, n))

    if start_idx >= end_idx:
        return []

    return tokens[start_idx:end_idx]


def register_tl_handlers(expander: ExpanderCore) -> None:
    """Register token list handlers."""
    # Creation
    for name in ["\\tl_new:N", "\\tl_clear_new:N"]:
        expander.register_handler(name, tl_new_handler, is_global=True)

    # Setting
    for name in ["\\tl_set:Nn", "\\tl_set:Nx", "\\tl_set:No"]:
        expander.register_handler(name, tl_set_handler, is_global=True)
    for name in ["\\tl_gset:Nn", "\\tl_gset:Nx", "\\tl_gset:No"]:
        expander.register_handler(name, tl_gset_handler, is_global=True)

    # Using
    expander.register_handler("\\tl_use:N", tl_use_handler, is_global=True)

    # Appending/prepending
    for name in ["\\tl_put_right:Nn", "\\tl_put_right:Nx"]:
        expander.register_handler(name, tl_put_right_handler, is_global=True)
    for name in ["\\tl_put_left:Nn", "\\tl_put_left:Nx"]:
        expander.register_handler(name, tl_put_left_handler, is_global=True)

    # Clearing
    for name in ["\\tl_clear:N", "\\tl_gclear:N"]:
        expander.register_handler(name, tl_clear_handler, is_global=True)

    # String conversion
    expander.register_handler("\\tl_to_str:n", tl_to_str_n_handler, is_global=True)
    expander.register_handler("\\tl_to_str:N", tl_to_str_N_handler, is_global=True)

    # Empty conditionals
    for name in ["\\tl_if_empty:nTF", "\\tl_if_empty:NTF"]:
        expander.register_handler(name, tl_if_empty_TF_handler, is_global=True)
    for name in ["\\tl_if_empty:nT", "\\tl_if_empty:NT"]:
        expander.register_handler(name, tl_if_empty_T_handler, is_global=True)
    for name in ["\\tl_if_empty:nF", "\\tl_if_empty:NF"]:
        expander.register_handler(name, tl_if_empty_F_handler, is_global=True)

    # Equality conditionals
    for name in ["\\tl_if_eq:nnTF", "\\tl_if_eq:NNTF"]:
        expander.register_handler(name, tl_if_eq_TF_handler, is_global=True)

    # Head/tail
    expander.register_handler("\\tl_head:n", tl_head_handler, is_global=True)
    expander.register_handler("\\tl_tail:n", tl_tail_handler, is_global=True)

    # Range extraction
    expander.register_handler("\\tl_range:nnn", tl_range_handler, is_global=True)
