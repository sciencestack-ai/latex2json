from typing import List, Optional
from latex2json.expander.handlers.if_else.base_if import parse_if_else_block_tokens
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token, TokenType
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.utils import split_tokens_by_predicate


def is_or_token(tok: Token) -> bool:
    return tok.type == TokenType.CONTROL_SEQUENCE and tok.value == "or"


def if_case_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    int_val = expander.parse_integer()
    blocks = parse_if_else_block_tokens(expander)
    if blocks is None:
        return []

    main_block = blocks[1]  # use the else block as default
    if int_val is not None:
        true_block = blocks[0]
        or_blocks = split_tokens_by_predicate(
            true_block,
            is_or_token,
        )
        total_cases = len(or_blocks)
        if 0 <= int_val < total_cases:
            main_block = or_blocks[int_val]

    return expander.expand_tokens(main_block)


def register_ifcase(expander: ExpanderCore):
    r"""Registers the \ifcase macro with the expander."""
    if_case_macro = Macro("ifcase", handler=if_case_handler, type=MacroType.IF)
    expander.register_macro("\\ifcase", if_case_macro, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    text = r"""
    \ifcase 2
    Case 0
    \or
    Case 1
    \or
    Case 2
    \else 
    Default
    \fi"""
    out = expander.expand(text)
