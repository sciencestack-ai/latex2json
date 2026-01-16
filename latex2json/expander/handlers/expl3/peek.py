r"""
expl3 peek handlers.

Handles \peek_catcode:NTF, \peek_meaning:NTF, and related commands
for examining the next token in the input stream.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token, TokenType


def peek_catcode_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \peek_catcode:NTF <test token> {<true code>} {<false code>}

    Tests if the next token in the input stream has the same catcode
    as the test token. Does not consume the peeked token.

    The peek happens BEFORE the branches are parsed - the peeked token
    is what comes right after the test token.
    """
    expander.skip_whitespace()
    test_token = expander.consume()

    # Peek at the next token (this is what we're testing)
    # Don't skip whitespace - we want to test whatever is next
    next_token = expander.peek()

    # Now parse the branches
    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if next_token and test_token:
        # Compare catcodes
        if next_token.catcode == test_token.catcode:
            expander.push_tokens(true_branch)
        else:
            expander.push_tokens(false_branch)
    else:
        # If we can't peek or have no test token, take false branch
        expander.push_tokens(false_branch)

    return []


def peek_catcode_T_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \peek_catcode:NT <test token> {<true code>}

    Tests if the next token has the same catcode as the test token.
    Only executes true branch if match.
    """
    expander.skip_whitespace()
    test_token = expander.consume()

    # Peek at the next token (before parsing branch)
    next_token = expander.peek()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    if next_token and test_token and next_token.catcode == test_token.catcode:
        expander.push_tokens(true_branch)

    return []


def peek_catcode_F_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \peek_catcode:NF <test token> {<false code>}

    Tests if the next token has the same catcode as the test token.
    Only executes false branch if no match.
    """
    expander.skip_whitespace()
    test_token = expander.consume()

    # Peek at the next token (before parsing branch)
    next_token = expander.peek()

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if not (next_token and test_token and next_token.catcode == test_token.catcode):
        expander.push_tokens(false_branch)

    return []


def peek_meaning_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \peek_meaning:NTF <test token> {<true code>} {<false code>}

    Tests if the next token in the input stream has the same meaning
    as the test token. For control sequences, this compares their definitions.
    Does not consume the peeked token.

    The peek happens BEFORE the branches are parsed.
    """
    expander.skip_whitespace()
    test_token = expander.consume()

    # Peek at the next token (before parsing branches)
    next_token = expander.peek()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if next_token and test_token:
        same_meaning = _tokens_have_same_meaning(expander, test_token, next_token)
        if same_meaning:
            expander.push_tokens(true_branch)
        else:
            expander.push_tokens(false_branch)
    else:
        expander.push_tokens(false_branch)

    return []


def peek_meaning_T_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \peek_meaning:NT <test token> {<true code>}

    Tests if the next token has the same meaning as the test token.
    Only executes true branch if match.
    """
    expander.skip_whitespace()
    test_token = expander.consume()

    # Peek at the next token (before parsing branch)
    next_token = expander.peek()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    if next_token and test_token:
        if _tokens_have_same_meaning(expander, test_token, next_token):
            expander.push_tokens(true_branch)

    return []


def peek_meaning_F_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \peek_meaning:NF <test token> {<false code>}

    Tests if the next token has the same meaning as the test token.
    Only executes false branch if no match.
    """
    expander.skip_whitespace()
    test_token = expander.consume()

    # Peek at the next token (before parsing branch)
    next_token = expander.peek()

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if not (
        next_token
        and test_token
        and _tokens_have_same_meaning(expander, test_token, next_token)
    ):
        expander.push_tokens(false_branch)

    return []


def _tokens_have_same_meaning(
    expander: ExpanderCore, token1: Token, token2: Token
) -> bool:
    """
    Check if two tokens have the same meaning.

    For character tokens: same value and catcode
    For control sequences: same definition (or both undefined)
    """
    # Different token types means different meaning
    if token1.type != token2.type:
        return False

    if token1.type == TokenType.CONTROL_SEQUENCE:
        # For control sequences, compare their definitions
        macro1 = expander.get_macro(token1)
        macro2 = expander.get_macro(token2)

        if macro1 is None and macro2 is None:
            # Both undefined - same meaning
            return True
        if macro1 is None or macro2 is None:
            # One defined, one not
            return False

        # Compare definitions
        def1 = macro1.definition or []
        def2 = macro2.definition or []

        if len(def1) != len(def2):
            return False

        return all(t1 == t2 for t1, t2 in zip(def1, def2))
    else:
        # For character tokens, compare value and catcode
        return token1.value == token2.value and token1.catcode == token2.catcode


def register_peek_handlers(expander: ExpanderCore) -> None:
    """Register peek handlers."""
    # peek_catcode variants
    expander.register_handler(
        "\\peek_catcode:NTF", peek_catcode_TF_handler, is_global=True
    )
    expander.register_handler(
        "\\peek_catcode:NT", peek_catcode_T_handler, is_global=True
    )
    expander.register_handler(
        "\\peek_catcode:NF", peek_catcode_F_handler, is_global=True
    )

    # peek_meaning variants
    expander.register_handler(
        "\\peek_meaning:NTF", peek_meaning_TF_handler, is_global=True
    )
    expander.register_handler(
        "\\peek_meaning:NT", peek_meaning_T_handler, is_global=True
    )
    expander.register_handler(
        "\\peek_meaning:NF", peek_meaning_F_handler, is_global=True
    )
