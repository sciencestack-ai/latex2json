r"""
expl3 token (l3token) handlers.

Handles \token_to_str:N, \token_to_meaning:N, \c_space_token, etc.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType


def token_to_str_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \token_to_str:N <token>  ->  string representation
    For control sequences, returns the name without backslash.
    """
    expander.skip_whitespace()
    tok = expander.consume()
    if tok:
        if tok.type == TokenType.CONTROL_SEQUENCE:
            return expander.convert_str_to_tokens(tok.value)
        else:
            return [tok]
    return []


def token_to_meaning_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \token_to_meaning:N <token>  ->  meaning of token
    Returns a textual representation of the token's meaning.
    """
    expander.skip_whitespace()
    tok = expander.consume()
    if tok:
        if tok.type == TokenType.CONTROL_SEQUENCE:
            macro = expander.get_macro(tok)
            if macro and macro.definition:
                return expander.convert_str_to_tokens("macro")
            return expander.convert_str_to_tokens("undefined")
        elif tok.type == TokenType.CHARACTER:
            return expander.convert_str_to_tokens(f"the character {tok.value}")
    return []


def c_space_token_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \c_space_token  ->  explicit space token
    """
    return [Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE)]


def c_catcode_letter_token_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \c_catcode_letter_token  ->  a token with letter catcode
    Used for comparisons.
    """
    return [Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER)]


def c_catcode_other_token_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \c_catcode_other_token  ->  a token with other catcode
    Used for comparisons.
    """
    return [Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER)]


def token_if_cs_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \token_if_cs:NTF <token> {true} {false}
    Tests if token is a control sequence.
    """
    expander.skip_whitespace()
    tok = expander.consume()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if tok and tok.type == TokenType.CONTROL_SEQUENCE:
        expander.push_tokens(true_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def register_token_handlers(expander: ExpanderCore) -> None:
    """Register l3token handlers."""
    # String conversion
    expander.register_handler("\\token_to_str:N", token_to_str_handler, is_global=True)
    expander.register_handler(
        "\\token_to_meaning:N", token_to_meaning_handler, is_global=True
    )

    # Constant tokens
    expander.register_handler("\\c_space_token", c_space_token_handler, is_global=True)
    expander.register_handler(
        "\\c_catcode_letter_token", c_catcode_letter_token_handler, is_global=True
    )
    expander.register_handler(
        "\\c_catcode_other_token", c_catcode_other_token_handler, is_global=True
    )

    # Type testing
    expander.register_handler(
        "\\token_if_cs:NTF", token_if_cs_TF_handler, is_global=True
    )
