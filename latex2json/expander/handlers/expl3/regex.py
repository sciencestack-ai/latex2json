r"""
expl3 regular expression (regex) handlers.

Handles \regex_new:N, \regex_set:Nn, \regex_match:nnTF, \regex_count:nnN,
\regex_replace_once:nnN, \regex_replace_all:nnN, and related functions.

Uses Python's re module for regex operations. The expl3 regex syntax is
similar to Perl regex, which Python's re module supports well.
"""

import re
from typing import Dict, List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType


def _make_brace_tokens(tokens: List[Token]) -> List[Token]:
    """Wrap tokens in braces."""
    return [
        Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
        *tokens,
        Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
    ]


def _tokens_to_str(tokens: List[Token]) -> str:
    """Convert tokens to string."""
    return "".join(t.value for t in tokens)


def _convert_expl3_regex(pattern: str) -> str:
    r"""
    Convert expl3 regex syntax to Python regex syntax.

    expl3 uses some special syntax:
    - \c{...} matches a control sequence
    - \u{var} uses the content of a variable
    - Most other syntax is similar to Perl/Python

    For simplicity, we do minimal conversion here.
    """
    # Remove common expl3 escapes that don't apply to Python
    # \c{...} -> just remove (we can't match control sequences easily)
    pattern = re.sub(r'\\c\{[^}]*\}', '', pattern)

    # Handle character classes - expl3 uses similar syntax to Perl
    # Most patterns should work directly

    return pattern


def regex_new_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \regex_new:N \l_my_regex
    Create a new regex variable (initialized to empty pattern).
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


def regex_set_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \regex_set:Nn \l_my_regex {pattern}
    Set a regex variable to a compiled pattern.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    pattern_tokens = expander.parse_brace_as_tokens() or []

    if var:
        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
            + _make_brace_tokens(pattern_tokens)
        )
    return []


def regex_match_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \regex_match:nnTF {regex} {string} {true} {false}
    Test if regex matches anywhere in string.
    """
    expander.skip_whitespace()
    pattern_tokens = expander.parse_brace_as_tokens() or []
    pattern = _tokens_to_str(pattern_tokens)

    expander.skip_whitespace()
    string_tokens = expander.parse_brace_as_tokens() or []
    string = _tokens_to_str(string_tokens)

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    try:
        py_pattern = _convert_expl3_regex(pattern)
        if re.search(py_pattern, string):
            expander.push_tokens(true_branch)
        else:
            expander.push_tokens(false_branch)
    except re.error:
        # Invalid regex - treat as no match
        expander.push_tokens(false_branch)

    return []


def regex_match_T_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \regex_match:nnT {regex} {string} {true}
    """
    expander.skip_whitespace()
    pattern_tokens = expander.parse_brace_as_tokens() or []
    pattern = _tokens_to_str(pattern_tokens)

    expander.skip_whitespace()
    string_tokens = expander.parse_brace_as_tokens() or []
    string = _tokens_to_str(string_tokens)

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    try:
        py_pattern = _convert_expl3_regex(pattern)
        if re.search(py_pattern, string):
            expander.push_tokens(true_branch)
    except re.error:
        pass

    return []


def regex_match_F_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \regex_match:nnF {regex} {string} {false}
    """
    expander.skip_whitespace()
    pattern_tokens = expander.parse_brace_as_tokens() or []
    pattern = _tokens_to_str(pattern_tokens)

    expander.skip_whitespace()
    string_tokens = expander.parse_brace_as_tokens() or []
    string = _tokens_to_str(string_tokens)

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    try:
        py_pattern = _convert_expl3_regex(pattern)
        if not re.search(py_pattern, string):
            expander.push_tokens(false_branch)
    except re.error:
        expander.push_tokens(false_branch)

    return []


def regex_count_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \regex_count:nnN {regex} {string} \l_count_int
    Count matches and store in integer variable.
    """
    expander.skip_whitespace()
    pattern_tokens = expander.parse_brace_as_tokens() or []
    pattern = _tokens_to_str(pattern_tokens)

    expander.skip_whitespace()
    string_tokens = expander.parse_brace_as_tokens() or []
    string = _tokens_to_str(string_tokens)

    expander.skip_whitespace()
    var = expander.consume()

    if var:
        try:
            py_pattern = _convert_expl3_regex(pattern)
            matches = re.findall(py_pattern, string)
            count = len(matches)
        except re.error:
            count = 0

        # Set the counter variable
        result = [var, Token(TokenType.CHARACTER, "=", catcode=Catcode.OTHER)]
        result.extend(expander.convert_str_to_tokens(str(count)))
        expander.push_tokens(result)

    return []


def regex_extract_once_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \regex_extract_once:nnN {regex} {string} \l_result_seq
    Extract first match into a sequence.
    """
    expander.skip_whitespace()
    pattern_tokens = expander.parse_brace_as_tokens() or []
    pattern = _tokens_to_str(pattern_tokens)

    expander.skip_whitespace()
    string_tokens = expander.parse_brace_as_tokens() or []
    string = _tokens_to_str(string_tokens)

    expander.skip_whitespace()
    var = expander.consume()

    if var:
        try:
            py_pattern = _convert_expl3_regex(pattern)
            match = re.search(py_pattern, string)
            if match:
                # Store the full match and any groups as sequence items
                groups = [match.group(0)] + list(match.groups())
                # Build sequence format: {item1}{item2}...
                seq_tokens = []
                for group in groups:
                    if group is not None:
                        seq_tokens.extend(_make_brace_tokens(
                            expander.convert_str_to_tokens(group)
                        ))
                expander.push_tokens(
                    [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
                    + _make_brace_tokens(seq_tokens)
                )
            else:
                # No match - empty sequence
                expander.push_tokens(
                    [
                        Token(TokenType.CONTROL_SEQUENCE, "def"),
                        var,
                        Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
                        Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
                    ]
                )
        except re.error:
            # Invalid regex - empty sequence
            expander.push_tokens(
                [
                    Token(TokenType.CONTROL_SEQUENCE, "def"),
                    var,
                    Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
                    Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
                ]
            )

    return []


def regex_replace_once_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \regex_replace_once:nnN {regex} {replacement} \l_str_tl
    Replace first match in the token list variable.
    """
    expander.skip_whitespace()
    pattern_tokens = expander.parse_brace_as_tokens() or []
    pattern = _tokens_to_str(pattern_tokens)

    expander.skip_whitespace()
    replacement_tokens = expander.parse_brace_as_tokens() or []
    replacement = _tokens_to_str(replacement_tokens)

    expander.skip_whitespace()
    var = expander.consume()

    if var:
        macro = expander.get_macro(var)
        if macro and macro.definition:
            string = _tokens_to_str(macro.definition)
            try:
                py_pattern = _convert_expl3_regex(pattern)
                # Convert expl3 replacement syntax (\0, \1) to Python (\g<0>, \1)
                py_replacement = replacement.replace(r'\0', r'\g<0>')
                result = re.sub(py_pattern, py_replacement, string, count=1)
                expander.push_tokens(
                    [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
                    + _make_brace_tokens(expander.convert_str_to_tokens(result))
                )
            except re.error:
                pass  # Invalid regex - do nothing

    return []


def regex_replace_all_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \regex_replace_all:nnN {regex} {replacement} \l_str_tl
    Replace all matches in the token list variable.
    """
    expander.skip_whitespace()
    pattern_tokens = expander.parse_brace_as_tokens() or []
    pattern = _tokens_to_str(pattern_tokens)

    expander.skip_whitespace()
    replacement_tokens = expander.parse_brace_as_tokens() or []
    replacement = _tokens_to_str(replacement_tokens)

    expander.skip_whitespace()
    var = expander.consume()

    if var:
        macro = expander.get_macro(var)
        if macro and macro.definition:
            string = _tokens_to_str(macro.definition)
            try:
                py_pattern = _convert_expl3_regex(pattern)
                py_replacement = replacement.replace(r'\0', r'\g<0>')
                result = re.sub(py_pattern, py_replacement, string)
                expander.push_tokens(
                    [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
                    + _make_brace_tokens(expander.convert_str_to_tokens(result))
                )
            except re.error:
                pass  # Invalid regex - do nothing

    return []


def regex_split_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \regex_split:nnN {regex} {string} \l_result_seq
    Split string by regex and store parts in sequence.
    """
    expander.skip_whitespace()
    pattern_tokens = expander.parse_brace_as_tokens() or []
    pattern = _tokens_to_str(pattern_tokens)

    expander.skip_whitespace()
    string_tokens = expander.parse_brace_as_tokens() or []
    string = _tokens_to_str(string_tokens)

    expander.skip_whitespace()
    var = expander.consume()

    if var:
        try:
            py_pattern = _convert_expl3_regex(pattern)
            parts = re.split(py_pattern, string)
            # Build sequence format: {part1}{part2}...
            seq_tokens = []
            for part in parts:
                seq_tokens.extend(_make_brace_tokens(
                    expander.convert_str_to_tokens(part)
                ))
            expander.push_tokens(
                [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
                + _make_brace_tokens(seq_tokens)
            )
        except re.error:
            # Invalid regex - just put original string as single item
            expander.push_tokens(
                [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
                + _make_brace_tokens(_make_brace_tokens(string_tokens))
            )

    return []


def register_regex_handlers(expander: ExpanderCore) -> None:
    """Register regex handlers."""
    # Creation
    expander.register_handler("\\regex_new:N", regex_new_handler, is_global=True)

    # Setting
    for name in ["\\regex_set:Nn", "\\regex_gset:Nn"]:
        expander.register_handler(name, regex_set_handler, is_global=True)

    # Matching
    expander.register_handler("\\regex_match:nnTF", regex_match_TF_handler, is_global=True)
    expander.register_handler("\\regex_match:nnT", regex_match_T_handler, is_global=True)
    expander.register_handler("\\regex_match:nnF", regex_match_F_handler, is_global=True)

    # Counting
    expander.register_handler("\\regex_count:nnN", regex_count_handler, is_global=True)

    # Extracting
    for name in ["\\regex_extract_once:nnN", "\\regex_extract_once:nnNTF"]:
        expander.register_handler(name, regex_extract_once_handler, is_global=True)

    # Replacing
    for name in ["\\regex_replace_once:nnN", "\\regex_replace_once:nnNTF"]:
        expander.register_handler(name, regex_replace_once_handler, is_global=True)
    for name in ["\\regex_replace_all:nnN", "\\regex_replace_all:nnNTF"]:
        expander.register_handler(name, regex_replace_all_handler, is_global=True)

    # Splitting
    expander.register_handler("\\regex_split:nnN", regex_split_handler, is_global=True)
