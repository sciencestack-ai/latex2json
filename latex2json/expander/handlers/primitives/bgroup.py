from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def bgroup_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.push_scope()
    return []


def egroup_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.pop_scope()
    return []


def register_bgroup(expander: ExpanderCore):
    expander.register_handler("\\bgroup", bgroup_handler, is_global=True)
    expander.register_handler("\\egroup", egroup_handler, is_global=True)
