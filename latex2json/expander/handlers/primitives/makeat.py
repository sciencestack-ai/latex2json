from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token


def make_at_letter_handler(
    expander: ExpanderCore, token: Token
) -> Optional[List[Token]]:
    expander.makeatletter()
    return []


def make_at_other_handler(
    expander: ExpanderCore, token: Token
) -> Optional[List[Token]]:
    expander.makeatother()
    return []


def register_makeat(expander: ExpanderCore):
    expander.register_handler("\\makeatletter", make_at_letter_handler, is_global=True)
    expander.register_handler("\\makeatother", make_at_other_handler, is_global=True)
