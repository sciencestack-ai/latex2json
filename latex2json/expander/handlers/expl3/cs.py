"""
expl3 control sequence (cs) handlers.

Handles \cs_new_eq:NN, \cs_new:Npn, \cs_if_exist:NTF, \cs_to_str:N,
\cs_generate_variant:Nn and related functions.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import wrap_tokens_in_braces


def cs_new_eq_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \cs_new_eq:NN \new \old  ->  \let\new\old
    """
    expander.skip_whitespace()
    new_cmd = expander.consume()
    expander.skip_whitespace()
    old_cmd = expander.consume()

    if new_cmd and old_cmd:
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "let"),
                new_cmd,
                old_cmd,
            ]
        )
    return []


def cs_gset_eq_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \cs_gset_eq:NN \new \old  ->  \global\let\new\old
    """
    expander.skip_whitespace()
    new_cmd = expander.consume()
    expander.skip_whitespace()
    old_cmd = expander.consume()

    if new_cmd and old_cmd:
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "global"),
                Token(TokenType.CONTROL_SEQUENCE, "let"),
                new_cmd,
                old_cmd,
            ]
        )
    return []


def cs_new_npn_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \cs_new:Npn \cmd #1#2 {body}  ->  \def\cmd#1#2{body}
    """
    from latex2json.tokens.catcodes import Catcode

    expander.skip_whitespace()
    cmd = expander.consume()
    if not cmd:
        return []

    # Collect param tokens until {
    param_tokens = []
    while True:
        tok = expander.peek()
        if tok is None or tok.catcode == Catcode.BEGIN_GROUP:
            break
        expander.consume()
        param_tokens.append(tok)

    # Get body (including braces)
    body_tokens = expander.parse_brace_as_tokens() or []

    # Push \def\cmd#1#2{body}
    expander.push_tokens(
        [Token(TokenType.CONTROL_SEQUENCE, "def"), cmd]
        + param_tokens
        + wrap_tokens_in_braces(body_tokens)
    )
    return []


def cs_if_exist_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \cs_if_exist:NTF \cmd {true} {false}
    """
    expander.skip_whitespace()
    cmd = expander.consume()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if cmd and expander.get_macro(cmd):
        expander.push_tokens(true_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def cs_if_free_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \cs_if_free:NTF \cmd {true} {false}
    Opposite of cs_if_exist - true if command is NOT defined.
    """
    expander.skip_whitespace()
    cmd = expander.consume()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if not cmd or not expander.get_macro(cmd):
        expander.push_tokens(true_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def cs_if_free_T_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \cs_if_free:NT \cmd {true}
    """
    expander.skip_whitespace()
    cmd = expander.consume()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    if not cmd or not expander.get_macro(cmd):
        expander.push_tokens(true_branch)
    return []


def cs_if_free_F_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \cs_if_free:NF \cmd {false}
    """
    expander.skip_whitespace()
    cmd = expander.consume()

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if cmd and expander.get_macro(cmd):
        expander.push_tokens(false_branch)
    return []


def cs_if_exist_T_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \cs_if_exist:NT \cmd {true}
    """
    expander.skip_whitespace()
    cmd = expander.consume()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    if cmd and expander.get_macro(cmd):
        expander.push_tokens(true_branch)
    return []


def cs_if_exist_F_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \cs_if_exist:NF \cmd {false}
    """
    expander.skip_whitespace()
    cmd = expander.consume()

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if not cmd or not expander.get_macro(cmd):
        expander.push_tokens(false_branch)
    return []


def cs_if_exist_use_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \cs_if_exist_use:NTF \cmd {true} {false}
    If \cmd exists, use it and execute true branch; otherwise false branch.
    """
    expander.skip_whitespace()
    cmd = expander.consume()

    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if cmd and expander.get_macro(cmd):
        expander.push_tokens(true_branch)
        expander.push_tokens([cmd])  # Use the command
    else:
        expander.push_tokens(false_branch)
    return []


def cs_to_str_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \cs_to_str:N \cmd -> "cmd" (name without backslash)
    """
    expander.skip_whitespace()
    cmd = expander.consume()
    if cmd and cmd.type == TokenType.CONTROL_SEQUENCE:
        return expander.convert_str_to_tokens(cmd.value)
    return []


def cs_generate_variant_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \cs_generate_variant:Nn \base:Nn {variants}

    This creates variant forms automatically. Since we register variants
    manually, this is mostly a no-op that consumes arguments.
    """
    expander.skip_whitespace()
    expander.consume()  # base command
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # variant specs
    return []


def cs_gset_Nn_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \cs_gset:Nn \cmd {body}  ->  \global\def\cmd{body}
    Globally sets a control sequence without parameters.
    """
    expander.skip_whitespace()
    cmd = expander.consume()
    expander.skip_whitespace()
    body_tokens = expander.parse_brace_as_tokens() or []

    if cmd:
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "global"),
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                cmd,
            ]
            + wrap_tokens_in_braces(body_tokens)
        )
    return []


def cs_new_cx_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \cs_new:cx {cmdname} {body}
    Creates a new command from constructed name with expanded body.
    """
    from latex2json.tokens.catcodes import Catcode

    expander.skip_whitespace()
    name_tokens = expander.parse_brace_as_tokens() or []
    cmd_name = "".join(t.value for t in name_tokens).strip()

    expander.skip_whitespace()
    body_tokens = expander.parse_brace_as_tokens() or []

    if cmd_name:
        cmd = Token(TokenType.CONTROL_SEQUENCE, cmd_name)
        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), cmd]
            + wrap_tokens_in_braces(body_tokens)
        )
    return []


def cs_set_cx_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \cs_set:cx {cmdname} {body}
    Sets a command from constructed name with expanded body.
    """
    return cs_new_cx_handler(expander, _token)


def cs_gset_cx_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \cs_gset:cx {cmdname} {body}
    Globally sets a command from constructed name with expanded body.
    """
    expander.skip_whitespace()
    name_tokens = expander.parse_brace_as_tokens() or []
    cmd_name = "".join(t.value for t in name_tokens).strip()

    expander.skip_whitespace()
    body_tokens = expander.parse_brace_as_tokens() or []

    if cmd_name:
        cmd = Token(TokenType.CONTROL_SEQUENCE, cmd_name)
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "global"),
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                cmd,
            ]
            + wrap_tokens_in_braces(body_tokens)
        )
    return []


def register_cs_handlers(expander: ExpanderCore) -> None:
    """Register control sequence handlers."""
    # \cs_new_eq:NN variants -> \let
    for name in ["\\cs_new_eq:NN", "\\cs_set_eq:NN"]:
        expander.register_handler(name, cs_new_eq_handler, is_global=True)

    for name in ["\\cs_gset_eq:NN", "\\cs_gnew_eq:NN"]:
        expander.register_handler(name, cs_gset_eq_handler, is_global=True)

    # \cs_new:Npn variants -> \def
    for name in [
        "\\cs_new:Npn",
        "\\cs_set:Npn",
        "\\cs_new_protected:Npn",
        "\\cs_set_protected:Npn",
        "\\cs_gset:Npn",
        "\\cs_gset_protected:Npn",
    ]:
        expander.register_handler(name, cs_new_npn_handler, is_global=True)

    # Existence checks
    for name in ["\\cs_if_exist:NTF", "\\cs_if_exist:cTF"]:
        expander.register_handler(name, cs_if_exist_TF_handler, is_global=True)
    for name in ["\\cs_if_exist:NT", "\\cs_if_exist:cT"]:
        expander.register_handler(name, cs_if_exist_T_handler, is_global=True)
    for name in ["\\cs_if_exist:NF", "\\cs_if_exist:cF"]:
        expander.register_handler(name, cs_if_exist_F_handler, is_global=True)
    expander.register_handler(
        "\\cs_if_exist_use:NTF", cs_if_exist_use_TF_handler, is_global=True
    )

    # Free checks (opposite of exist)
    for name in ["\\cs_if_free:NTF", "\\cs_if_free:cTF"]:
        expander.register_handler(name, cs_if_free_TF_handler, is_global=True)
    for name in ["\\cs_if_free:NT", "\\cs_if_free:cT"]:
        expander.register_handler(name, cs_if_free_T_handler, is_global=True)
    for name in ["\\cs_if_free:NF", "\\cs_if_free:cF"]:
        expander.register_handler(name, cs_if_free_F_handler, is_global=True)

    # Global set without parameters
    for name in ["\\cs_gset:Nn", "\\cs_gset:cn"]:
        expander.register_handler(name, cs_gset_Nn_handler, is_global=True)

    # cx variants (construct name, expand body)
    for name in ["\\cs_new:cx", "\\cs_new_protected:cx"]:
        expander.register_handler(name, cs_new_cx_handler, is_global=True)
    for name in ["\\cs_set:cx", "\\cs_set_protected:cx"]:
        expander.register_handler(name, cs_set_cx_handler, is_global=True)
    for name in ["\\cs_gset:cx", "\\cs_gset_protected:cx"]:
        expander.register_handler(name, cs_gset_cx_handler, is_global=True)

    # Utilities
    expander.register_handler("\\cs_to_str:N", cs_to_str_handler, is_global=True)
    expander.register_handler(
        "\\cs_generate_variant:Nn", cs_generate_variant_handler, is_global=True
    )
