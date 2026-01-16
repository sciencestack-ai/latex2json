"""
expl3 syntax mode handlers.

Handles \ExplSyntaxOn, \ExplSyntaxOff, \ProvidesExplPackage, \ProvidesExplClass
which control the expl3 programming syntax mode.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token


def _enable_expl3_syntax(expander: ExpanderCore) -> None:
    """Enable expl3 catcode settings."""
    expander.set_catcode(ord("_"), Catcode.LETTER)
    expander.set_catcode(ord(":"), Catcode.LETTER)
    expander.set_catcode(ord(" "), Catcode.IGNORED)
    expander.set_catcode(ord("\t"), Catcode.IGNORED)
    expander.set_catcode(ord("~"), Catcode.SPACE)


def _disable_expl3_syntax(expander: ExpanderCore) -> None:
    """Restore default catcode settings."""
    expander.set_catcode(ord("_"), Catcode.SUBSCRIPT)
    expander.set_catcode(ord(":"), Catcode.OTHER)
    expander.set_catcode(ord(" "), Catcode.SPACE)
    expander.set_catcode(ord("\t"), Catcode.SPACE)
    expander.set_catcode(ord("~"), Catcode.ACTIVE)


def expl_syntax_on_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    Handle \ExplSyntaxOn - enable expl3 syntax mode.

    Changes catcodes:
    - _ (underscore) -> LETTER (11) - becomes part of command names
    - : (colon) -> LETTER (11) - becomes part of command names
    - space -> IGNORED (9) - spaces are ignored in expl3 code
    - ~ (tilde) -> SPACE (10) - ~ produces a space in expl3
    """
    _enable_expl3_syntax(expander)
    return []


def expl_syntax_off_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    Handle \ExplSyntaxOff - disable expl3 syntax mode.

    Restores default catcodes:
    - _ (underscore) -> SUBSCRIPT (8)
    - : (colon) -> OTHER (12)
    - space -> SPACE (10)
    - ~ (tilde) -> ACTIVE (13)
    """
    _disable_expl3_syntax(expander)
    return []


def provides_expl_package_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    Handle \ProvidesExplPackage{name}{date}{version}{description}

    This implicitly enables expl3 syntax for the rest of the package.
    """
    # Consume the 4 required arguments: {name}{date}{version}{description}
    for _ in range(4):
        expander.skip_whitespace()
        expander.parse_brace_as_tokens()

    _enable_expl3_syntax(expander)
    return []


def provides_expl_class_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    Handle \ProvidesExplClass{name}{date}{version}{description}

    This implicitly enables expl3 syntax for the rest of the class.
    """
    return provides_expl_package_handler(expander, _token)


def register_syntax_handlers(expander: ExpanderCore) -> None:
    """Register expl3 syntax handlers."""
    expander.register_handler("\\ExplSyntaxOn", expl_syntax_on_handler, is_global=True)
    expander.register_handler(
        "\\ExplSyntaxOff", expl_syntax_off_handler, is_global=True
    )
    expander.register_handler(
        "\\ProvidesExplPackage", provides_expl_package_handler, is_global=True
    )
    expander.register_handler(
        "\\ProvidesExplClass", provides_expl_class_handler, is_global=True
    )
