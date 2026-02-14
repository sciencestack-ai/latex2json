r"""
expl3 io (l3io) handlers.

Handles \iow_now:Nn, \iow_now:Nx, \ior_*, etc.
These deal with input/output streams.

For parsing purposes, we mostly ignore output operations since
we're not producing any actual output.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def iow_now_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \iow_now:Nn <stream> {content}
    \iow_now:Nx <stream> {content}
    Writes to output stream. We ignore this.
    """
    expander.skip_whitespace()
    expander.consume()  # stream
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # content to write
    return []


def iow_log_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \iow_log:n {content}
    Writes to log. We ignore this.
    """
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # content
    return []


def iow_term_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \iow_term:n {content}
    Writes to terminal. We ignore this.
    """
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # content
    return []


def iow_shipout_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \iow_shipout:Nn <stream> {content}
    Writes to output stream at shipout. We ignore this.
    """
    expander.skip_whitespace()
    expander.consume()  # stream
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # content
    return []


def iow_open_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \iow_open:Nn <stream> {filename}
    Opens an output stream. We ignore this.
    """
    expander.skip_whitespace()
    expander.consume()  # stream variable
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # filename
    return []


def iow_close_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \iow_close:N <stream>
    Closes an output stream. We ignore this.
    """
    expander.skip_whitespace()
    expander.consume()  # stream variable
    return []


def ior_open_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \ior_open:Nn <stream> {filename}
    Opens an input stream. We ignore this.
    """
    expander.skip_whitespace()
    expander.consume()  # stream variable
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # filename
    return []


def ior_close_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \ior_close:N <stream>
    Closes an input stream. We ignore this.
    """
    expander.skip_whitespace()
    expander.consume()  # stream variable
    return []


def register_io_handlers(expander: ExpanderCore) -> None:
    """Register l3io handlers."""
    # Output write - now
    for name in ["\\iow_now:Nn", "\\iow_now:Nx", "\\iow_now:NV", "\\iow_now:Ne"]:
        expander.register_handler(name, iow_now_handler, is_global=True)

    # Log and terminal
    for name in ["\\iow_log:n", "\\iow_log:x", "\\iow_log:e"]:
        expander.register_handler(name, iow_log_handler, is_global=True)
    for name in ["\\iow_term:n", "\\iow_term:x", "\\iow_term:e"]:
        expander.register_handler(name, iow_term_handler, is_global=True)

    # Shipout
    for name in ["\\iow_shipout:Nn", "\\iow_shipout:Nx"]:
        expander.register_handler(name, iow_shipout_handler, is_global=True)

    # Stream management
    for name in ["\\iow_open:Nn", "\\iow_open:cn"]:
        expander.register_handler(name, iow_open_handler, is_global=True)
    expander.register_handler("\\iow_close:N", iow_close_handler, is_global=True)
    for name in ["\\ior_open:Nn", "\\ior_open:cn"]:
        expander.register_handler(name, ior_open_handler, is_global=True)
    expander.register_handler("\\ior_close:N", ior_close_handler, is_global=True)
