from typing import List, Optional
from latex2json.expander.handlers.primitives.csname import process_csname_block
from latex2json.tokens.types import Token, TokenType
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.if_else.base_if import IfMacro
from latex2json.tokens.utils import strip_whitespace_tokens


def evaluate_ifcsname(
    expander: ExpanderCore, token: Token
) -> tuple[bool | None, str | None]:

    block = process_csname_block(expander)
    if block is None:
        return None, "\\ifcsname expects a block"

    str_name = expander.convert_tokens_to_str(block)
    control_sequence = Token(TokenType.CONTROL_SEQUENCE, str_name)
    # if exists
    is_true = expander.get_macro(control_sequence) is not None
    return is_true, None


def register_ifcsname(expander: ExpanderCore):
    expander.register_macro(
        "\\ifcsname", IfMacro("ifcsname", evaluate_ifcsname), is_global=True
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    text = r"""
\def\foo{foo}

\ifcsname foo\endcsname TRUE \else FALSE \fi % TRUE
\ifcsname xyzz\endcsname TRUE \else FALSE \fi % FALSE
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
