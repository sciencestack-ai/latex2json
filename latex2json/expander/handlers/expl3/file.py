r"""
expl3 file (l3file) handlers.

Handles \file_if_exist:nTF, \file_input:n, etc.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def file_if_exist_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \file_if_exist:nTF {filename} {true} {false}
    Tests if a file exists. Since we can't check, take false branch.
    """
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # filename

    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # true branch (ignore)

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    expander.push_tokens(false_branch)
    return []


def file_if_exist_T_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \file_if_exist:nT {filename} {true}
    Tests if a file exists. Since we can't check, do nothing.
    """
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # filename

    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # true branch (ignore)

    return []


def file_if_exist_F_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \file_if_exist:nF {filename} {false}
    Tests if a file exists. Since we can't check, take false branch.
    """
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # filename

    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    expander.push_tokens(false_branch)
    return []


def file_input_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \file_input:n {filename}
    Inputs a file. We just consume the argument since we can't read files.
    """
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # filename
    return []


def file_get_full_name_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \file_get_full_name:nN {filename} \l_result_tl
    Gets the full path of a file. We just return the filename unchanged.
    """
    expander.skip_whitespace()
    filename_tokens = expander.parse_brace_as_tokens() or []

    expander.skip_whitespace()
    result_var = expander.consume()

    if result_var:
        # Set the result variable to the filename
        from latex2json.tokens.catcodes import Catcode
        from latex2json.tokens.types import TokenType

        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                result_var,
                Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
            ]
            + filename_tokens
            + [Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP)]
        )
    return []


def register_file_handlers(expander: ExpanderCore) -> None:
    """Register l3file handlers."""
    # Existence tests
    for name in ["\\file_if_exist:nTF", "\\file_if_exist:VTF"]:
        expander.register_handler(name, file_if_exist_TF_handler, is_global=True)
    for name in ["\\file_if_exist:nT", "\\file_if_exist:VT"]:
        expander.register_handler(name, file_if_exist_T_handler, is_global=True)
    for name in ["\\file_if_exist:nF", "\\file_if_exist:VF"]:
        expander.register_handler(name, file_if_exist_F_handler, is_global=True)

    # File input
    for name in ["\\file_input:n", "\\file_input:V"]:
        expander.register_handler(name, file_input_handler, is_global=True)

    # Get full name
    expander.register_handler(
        "\\file_get_full_name:nN", file_get_full_name_handler, is_global=True
    )
