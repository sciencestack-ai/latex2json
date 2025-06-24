from typing import List, Optional
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token
from latex2json.expander.expander_core import ExpanderCore


def if_case_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:

    return []


def register_ifcase(expander: ExpanderCore):
    r"""Registers the \ifcase macro with the expander."""
    if_case_macro = Macro("ifcase", handler=if_case_handler, type=MacroType.IF)
    expander.register_macro("\\ifcase", if_case_macro, is_global=True)
