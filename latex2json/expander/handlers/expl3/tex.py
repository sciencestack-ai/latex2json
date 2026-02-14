r"""
expl3 TeX primitive access handlers.

Handles \tex_def:D, \tex_xdef:D, \tex_let:D, \tex_gdef:D, etc.
These provide access to TeX primitives with expl3 naming conventions.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token, TokenType


def tex_def_D_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \tex_def:D  ->  \def
    Just push the \def primitive.
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "def")])
    return []


def tex_edef_D_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \tex_edef:D  ->  \edef
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "edef")])
    return []


def tex_gdef_D_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \tex_gdef:D  ->  \gdef
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "gdef")])
    return []


def tex_xdef_D_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \tex_xdef:D  ->  \xdef
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "xdef")])
    return []


def tex_let_D_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \tex_let:D  ->  \let
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "let")])
    return []


def tex_global_D_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tex_global:D  ->  \global
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "global")])
    return []


def tex_advance_D_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tex_advance:D  ->  \advance
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "advance")])
    return []


def tex_the_D_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \tex_the:D  ->  \the
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "the")])
    return []


def tex_relax_D_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tex_relax:D  ->  \relax
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "relax")])
    return []


def tex_newcount_D_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tex_newcount:D  ->  \newcount
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "newcount")])
    return []


def tex_expandafter_D_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tex_expandafter:D  ->  \expandafter
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "expandafter")])
    return []


def tex_noexpand_D_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tex_noexpand:D  ->  \noexpand
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "noexpand")])
    return []


def tex_number_D_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tex_number:D  ->  \number
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "number")])
    return []


def tex_string_D_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tex_string:D  ->  \string
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "string")])
    return []


def tex_csname_D_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tex_csname:D  ->  \csname
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "csname")])
    return []


def tex_endcsname_D_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tex_endcsname:D  ->  \endcsname
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "endcsname")])
    return []


def tex_chardef_D_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tex_chardef:D  ->  \chardef
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "chardef")])
    return []


def tex_mathchardef_D_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \tex_mathchardef:D  ->  \mathchardef
    """
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "mathchardef")])
    return []


def register_tex_handlers(expander: ExpanderCore) -> None:
    """Register TeX primitive access handlers."""
    # Definition primitives
    expander.register_handler("\\tex_def:D", tex_def_D_handler, is_global=True)
    expander.register_handler("\\tex_edef:D", tex_edef_D_handler, is_global=True)
    expander.register_handler("\\tex_gdef:D", tex_gdef_D_handler, is_global=True)
    expander.register_handler("\\tex_xdef:D", tex_xdef_D_handler, is_global=True)
    expander.register_handler("\\tex_let:D", tex_let_D_handler, is_global=True)

    # Prefix primitives
    expander.register_handler("\\tex_global:D", tex_global_D_handler, is_global=True)

    # Arithmetic primitives
    expander.register_handler("\\tex_advance:D", tex_advance_D_handler, is_global=True)

    # Expansion primitives
    expander.register_handler("\\tex_the:D", tex_the_D_handler, is_global=True)
    expander.register_handler("\\tex_relax:D", tex_relax_D_handler, is_global=True)
    expander.register_handler(
        "\\tex_expandafter:D", tex_expandafter_D_handler, is_global=True
    )
    expander.register_handler("\\tex_noexpand:D", tex_noexpand_D_handler, is_global=True)
    expander.register_handler("\\tex_number:D", tex_number_D_handler, is_global=True)
    expander.register_handler("\\tex_string:D", tex_string_D_handler, is_global=True)

    # Csname primitives
    expander.register_handler("\\tex_csname:D", tex_csname_D_handler, is_global=True)
    expander.register_handler(
        "\\tex_endcsname:D", tex_endcsname_D_handler, is_global=True
    )

    # Register primitives
    expander.register_handler(
        "\\tex_newcount:D", tex_newcount_D_handler, is_global=True
    )

    # Char definition primitives
    expander.register_handler("\\tex_chardef:D", tex_chardef_D_handler, is_global=True)
    expander.register_handler(
        "\\tex_mathchardef:D", tex_mathchardef_D_handler, is_global=True
    )
