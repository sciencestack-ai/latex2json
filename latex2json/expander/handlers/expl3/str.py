r"""
expl3 string (str) handlers.

Handles \str_if_eq:nnTF, \str_case:nnF, \str_set:Nn, etc.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.expl3._tf_factory import make_conditional_handlers
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType


# =============================================================================
# \str_set:... - String variable assignment
# =============================================================================


def str_set_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \str_set:Nn \l_my_str {content}  ->  \def\l_my_str{content}
    Sets a string variable to the given content.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    content = expander.parse_brace_as_tokens() or []

    if var:
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
                Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
            ]
            + content
            + [Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP)]
        )
    return []


def str_set_V_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \str_set:NV \l_my_str \l_other_var
    Sets a string variable to the value of another variable.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    source_var = expander.consume()

    if var and source_var:
        # Get the value of the source variable
        macro = expander.get_macro(source_var)
        content = macro.definition if macro and macro.definition else []

        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
                Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
            ]
            + list(content)
            + [Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP)]
        )
    return []


# =============================================================================
# \str_if_eq:... - String equality conditionals
# =============================================================================


def _eval_str_if_eq(expander: ExpanderCore, _token: Token) -> bool:
    r"""Evaluate \str_if_eq — parse two brace args and compare."""
    expander.skip_whitespace()
    str1_tokens = expander.parse_brace_as_tokens() or []
    str1 = "".join(t.value for t in str1_tokens)
    expander.skip_whitespace()
    str2_tokens = expander.parse_brace_as_tokens() or []
    str2 = "".join(t.value for t in str2_tokens)
    return str1 == str2


str_if_eq_TF_handler, str_if_eq_T_handler, str_if_eq_F_handler = (
    make_conditional_handlers(_eval_str_if_eq)
)


# =============================================================================
# \str_if_in:... - String containment conditionals
# =============================================================================


def str_if_in_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \str_if_in:nnTF {haystack} {needle} {true} {false}
    Tests if needle is contained in haystack.
    """
    expander.skip_whitespace()
    haystack_tokens = expander.parse_brace_as_tokens() or []
    haystack = "".join(t.value for t in haystack_tokens)

    expander.skip_whitespace()
    needle_tokens = expander.parse_brace_as_tokens() or []
    needle = "".join(t.value for t in needle_tokens)

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if needle in haystack:
        expander.push_tokens(true_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def str_if_in_nVTF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \str_if_in:nVTF {haystack} \l_needle_var {true} {false}
    Tests if needle (from variable) is contained in haystack.
    """
    expander.skip_whitespace()
    haystack_tokens = expander.parse_brace_as_tokens() or []
    haystack = "".join(t.value for t in haystack_tokens)

    expander.skip_whitespace()
    needle_var = expander.consume()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    needle = ""
    if needle_var:
        macro = expander.get_macro(needle_var)
        if macro and macro.definition:
            needle = "".join(t.value for t in macro.definition)

    if needle in haystack:
        expander.push_tokens(true_branch)
    else:
        expander.push_tokens(false_branch)
    return []


# =============================================================================
# \str_head:... - String head extraction
# =============================================================================


def str_head_ignore_spaces_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \str_head_ignore_spaces:n {string}
    Returns the first non-space character of the string.
    """
    expander.skip_whitespace()
    str_tokens = expander.parse_brace_as_tokens() or []
    string = "".join(t.value for t in str_tokens)

    # Find first non-space character
    for char in string:
        if not char.isspace():
            return expander.convert_str_to_tokens(char)

    return []


# =============================================================================
# \str_case:... - String pattern matching
# =============================================================================


def str_case_F_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \str_case:nnF {test} { {val1}{result1} ... } {false}

    String pattern matching with false branch.
    """
    expander.skip_whitespace()
    test_tokens = expander.parse_brace_as_tokens() or []
    test_str = "".join(t.value for t in test_tokens).strip()

    expander.skip_whitespace()
    cases_tokens = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    # Push cases tokens back onto stream and parse {key}{value} pairs
    expander.push_tokens(cases_tokens)

    matched_value = None
    while expander.peek():
        expander.skip_whitespace()
        if not expander.peek() or expander.peek().catcode != Catcode.BEGIN_GROUP:
            break

        pair = expander.parse_braced_blocks(N_blocks=2)
        if len(pair) < 2:
            break

        key_tokens, value_tokens = pair
        key_str = "".join(t.value for t in key_tokens).strip()

        if matched_value is None and key_str == test_str:
            matched_value = value_tokens
            # Continue parsing to consume remaining cases

    # Push result after consuming all cases
    if matched_value is not None:
        expander.push_tokens(matched_value)
    else:
        expander.push_tokens(false_branch)
    return []


def str_case_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \str_case:nn {test} { {val1}{result1} ... }

    String pattern matching without default branch.
    """
    expander.skip_whitespace()
    test_tokens = expander.parse_brace_as_tokens() or []
    test_str = "".join(t.value for t in test_tokens).strip()

    expander.skip_whitespace()
    cases_tokens = expander.parse_brace_as_tokens() or []

    # Push cases tokens back onto stream and parse {key}{value} pairs
    expander.push_tokens(cases_tokens)

    matched_value = None
    while expander.peek():
        expander.skip_whitespace()
        if not expander.peek() or expander.peek().catcode != Catcode.BEGIN_GROUP:
            break

        pair = expander.parse_braced_blocks(N_blocks=2)
        if len(pair) < 2:
            break

        key_tokens, value_tokens = pair
        key_str = "".join(t.value for t in key_tokens).strip()

        if matched_value is None and key_str == test_str:
            matched_value = value_tokens
            # Continue parsing to consume remaining cases

    # Push result if we found a match
    if matched_value is not None:
        expander.push_tokens(matched_value)
    return []


def register_str_handlers(expander: ExpanderCore) -> None:
    """Register string handlers."""
    # String variable assignment
    for name in ["\\str_set:Nn", "\\str_set:Nx"]:
        expander.register_handler(name, str_set_handler, is_global=True)
    expander.register_handler("\\str_set:NV", str_set_V_handler, is_global=True)

    # Equality conditionals
    for name in ["\\str_if_eq:nnTF", "\\str_if_eq:VnTF", "\\str_if_eq:eeTF"]:
        expander.register_handler(name, str_if_eq_TF_handler, is_global=True)
    for name in ["\\str_if_eq:nnT", "\\str_if_eq:VnT", "\\str_if_eq:eeT"]:
        expander.register_handler(name, str_if_eq_T_handler, is_global=True)
    for name in ["\\str_if_eq:nnF", "\\str_if_eq:VnF", "\\str_if_eq:eeF"]:
        expander.register_handler(name, str_if_eq_F_handler, is_global=True)

    # Containment conditionals
    expander.register_handler("\\str_if_in:nnTF", str_if_in_TF_handler, is_global=True)
    expander.register_handler("\\str_if_in:nVTF", str_if_in_nVTF_handler, is_global=True)

    # Head extraction
    expander.register_handler(
        "\\str_head_ignore_spaces:n", str_head_ignore_spaces_handler, is_global=True
    )

    # Case matching
    for name in ["\\str_case:nn", "\\str_case:on", "\\str_case:Vn", "\\str_case:en"]:
        expander.register_handler(name, str_case_handler, is_global=True)
    for name in ["\\str_case:nnF", "\\str_case:onF", "\\str_case:VnF"]:
        expander.register_handler(name, str_case_F_handler, is_global=True)
