"""
expl3 boolean (bool) handlers.

Handles \bool_new:N, \bool_set_true:N, \bool_set_false:N, \bool_if:NTF, etc.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType


def bool_new_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \bool_new:N \l_my_bool  ->  \def\l_my_bool{0}
    """
    expander.skip_whitespace()
    var = expander.consume()
    if var:
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
                Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
                Token(TokenType.CHARACTER, "0", catcode=Catcode.OTHER),
                Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
            ]
        )
    return []


def bool_set_true_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \bool_set_true:N \l_my_bool  ->  \def\l_my_bool{1}
    """
    expander.skip_whitespace()
    var = expander.consume()
    if var:
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
                Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
                Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
                Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
            ]
        )
    return []


def bool_set_false_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \bool_set_false:N \l_my_bool  ->  \def\l_my_bool{0}
    """
    expander.skip_whitespace()
    var = expander.consume()
    if var:
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
                Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
                Token(TokenType.CHARACTER, "0", catcode=Catcode.OTHER),
                Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
            ]
        )
    return []


def bool_if_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \bool_if:NTF \l_my_bool {true} {false}
    """
    expander.skip_whitespace()
    var = expander.consume()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    # Check if bool is true (non-zero)
    is_true = False
    if var:
        macro = expander.get_macro(var)
        if macro and macro.definition:
            val_str = "".join(t.value for t in macro.definition).strip()
            is_true = val_str not in ("0", "", "false")

    if is_true:
        expander.push_tokens(true_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def register_bool_handlers(expander: ExpanderCore) -> None:
    """Register boolean handlers."""
    expander.register_handler("\\bool_new:N", bool_new_handler, is_global=True)
    expander.register_handler(
        "\\bool_set_true:N", bool_set_true_handler, is_global=True
    )
    expander.register_handler(
        "\\bool_set_false:N", bool_set_false_handler, is_global=True
    )
    for name in ["\\bool_if:NTF", "\\bool_if:nTF"]:
        expander.register_handler(name, bool_if_TF_handler, is_global=True)
