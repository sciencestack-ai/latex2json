r"""
expl3 skip (l3skip) handlers.

Handles \skip_horizontal:n, \skip_vertical:n, \skip_new:N, etc.
Skips are similar to dimensions but can include plus/minus glue components.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token, TokenType


def skip_horizontal_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \skip_horizontal:n {10pt}
    Horizontal skip. We push \hskip equivalent.
    """
    expander.skip_whitespace()
    value_tokens = expander.parse_brace_as_tokens() or []

    # Push \hskip <value>
    result = [Token(TokenType.CONTROL_SEQUENCE, "hskip")]
    result.extend(value_tokens)
    expander.push_tokens(result)
    return []


def skip_vertical_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \skip_vertical:n {10pt}
    Vertical skip. We push \vskip equivalent.
    """
    expander.skip_whitespace()
    value_tokens = expander.parse_brace_as_tokens() or []

    # Push \vskip <value>
    result = [Token(TokenType.CONTROL_SEQUENCE, "vskip")]
    result.extend(value_tokens)
    expander.push_tokens(result)
    return []


def skip_new_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \skip_new:N \l_my_skip
    Create a new skip register. We push \newskip.
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "newskip"), var])
    return []


def skip_set_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \skip_set:Nn \l_my_skip {10pt plus 2pt minus 1pt}
    Set a skip register value.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    value_tokens = expander.parse_brace_as_tokens() or []

    if var:
        from latex2json.tokens.catcodes import Catcode

        result = [var, Token(TokenType.CHARACTER, "=", catcode=Catcode.OTHER)]
        result.extend(value_tokens)
        expander.push_tokens(result)
    return []


def skip_zero_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \skip_zero:N \l_my_skip
    Set a skip register to zero.
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        from latex2json.tokens.catcodes import Catcode

        result = [
            var,
            Token(TokenType.CHARACTER, "=", catcode=Catcode.OTHER),
        ]
        result.extend(expander.convert_str_to_tokens("0pt"))
        expander.push_tokens(result)
    return []


def skip_use_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \skip_use:N \l_my_skip
    Use (output) a skip register value.
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "the"), var])
    return []


def register_skip_handlers(expander: ExpanderCore) -> None:
    """Register skip handlers."""
    # Horizontal and vertical skips
    for name in ["\\skip_horizontal:n", "\\skip_horizontal:N"]:
        expander.register_handler(name, skip_horizontal_handler, is_global=True)
    for name in ["\\skip_vertical:n", "\\skip_vertical:N"]:
        expander.register_handler(name, skip_vertical_handler, is_global=True)

    # Creation
    expander.register_handler("\\skip_new:N", skip_new_handler, is_global=True)

    # Setting
    for name in ["\\skip_set:Nn", "\\skip_gset:Nn"]:
        expander.register_handler(name, skip_set_handler, is_global=True)

    # Zeroing
    for name in ["\\skip_zero:N", "\\skip_gzero:N"]:
        expander.register_handler(name, skip_zero_handler, is_global=True)

    # Using
    for name in ["\\skip_use:N", "\\skip_use:c"]:
        expander.register_handler(name, skip_use_handler, is_global=True)
