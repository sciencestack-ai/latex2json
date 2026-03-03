"""
expl3 syntax mode handlers.

Handles \ExplSyntaxOn, \ExplSyntaxOff, \ProvidesExplPackage, \ProvidesExplClass
which control the expl3 programming syntax mode.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType


def _enable_expl3_syntax(expander: ExpanderCore) -> None:
    """Enable expl3 catcode settings."""
    expander.set_catcode(ord("_"), Catcode.LETTER)
    expander.set_catcode(ord(":"), Catcode.LETTER)
    expander.set_catcode(ord(" "), Catcode.IGNORED)
    expander.set_catcode(ord("\t"), Catcode.IGNORED)
    expander.set_catcode(ord("~"), Catcode.SPACE)


def _remerge_expl3_tokens_in_source(expander: ExpanderCore) -> None:
    r"""Re-merge split expl3 control sequences in pre-tokenized token sources.

    When \ExplSyntaxOn appears inside a conditional branch (\if...\else...\fi),
    the branch tokens are pre-tokenized before \ExplSyntaxOn fires. This means
    expl3 names like \bool_lazy_and:nnTF get split into \bool + _ + l + a + z + ...

    This function scans remaining tokens in the current TokenListSource and merges
    these split sequences back into single control sequence tokens.
    """
    from latex2json.tokens.token_stream import TokenListSource

    # Find the active TokenListSource on the stream stack
    source = None
    for s in reversed(expander.stream.source_stack):
        if isinstance(s, TokenListSource) and not s.eof():
            source = s
            break

    if source is None:
        return

    tokens = source.tokens
    idx = source.index
    if idx >= len(tokens):
        return

    # Scan and merge split expl3 control sequences in remaining tokens
    new_tokens = tokens[:idx]  # Keep already-consumed tokens as-is
    i = idx

    while i < len(tokens):
        tok = tokens[i]

        # Look for pattern: CS token followed by _ or : characters
        if tok.type == TokenType.CONTROL_SEQUENCE and i + 1 < len(tokens):
            next_tok = tokens[i + 1]
            # Check if next token is _ or : (which should be part of the CS name)
            if (
                next_tok.type == TokenType.CHARACTER
                and next_tok.value in ("_", ":")
                and next_tok.catcode != Catcode.LETTER  # Only fix wrongly-catcoded ones
            ):
                # Merge: collect CS name + all following _ : and letter chars
                merged_name = tok.value
                j = i + 1
                while j < len(tokens):
                    t = tokens[j]
                    if t.type == TokenType.CHARACTER and t.value in ("_", ":"):
                        merged_name += t.value
                        j += 1
                    elif t.type == TokenType.CHARACTER and t.catcode == Catcode.LETTER:
                        merged_name += t.value
                        j += 1
                    else:
                        break

                # Only merge if we actually absorbed _ or : chars
                if len(merged_name) > len(tok.value):
                    merged_tok = Token(TokenType.CONTROL_SEQUENCE, merged_name)
                    merged_tok.source_file = tok.source_file
                    merged_tok.position = tok.position
                    new_tokens.append(merged_tok)
                    i = j
                    continue

        new_tokens.append(tok)
        i += 1

    # Replace the token list in-place
    source.tokens = new_tokens


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
    _remerge_expl3_tokens_in_source(expander)
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
