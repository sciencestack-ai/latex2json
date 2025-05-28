from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token


def begingroup_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.push_scope()
    return []


def endgroup_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.pop_scope()
    return []


def bgroup_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.push_tokens([BEGIN_BRACE_TOKEN.copy()])
    return []


def egroup_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.push_tokens([END_BRACE_TOKEN.copy()])
    return []


# useful to define Macro as type=MacroType.CHAR so that it can be used in \ifx etc
def register_bgroup(expander: ExpanderCore):
    expander.register_macro(
        "bgroup",
        Macro(
            "bgroup",
            bgroup_handler,
            definition=[BEGIN_BRACE_TOKEN.copy()],
            type=MacroType.CHAR,
        ),
        is_global=True,
    )
    expander.register_macro(
        "egroup",
        Macro(
            "egroup",
            egroup_handler,
            definition=[END_BRACE_TOKEN.copy()],
            type=MacroType.CHAR,
        ),
        is_global=True,
    )

    expander.register_handler("begingroup", begingroup_handler, is_global=True)
    expander.register_handler("endgroup", endgroup_handler, is_global=True)
