from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.nodes.base import ASTNode
from latex2json.nodes.syntactic_nodes import CommandNode
from latex2json.tokens.catcodes import Catcode


def make_at_letter_handler(
    expander: ExpanderCore, node: CommandNode
) -> Optional[List[ASTNode]]:
    expander.set_catcode(ord("@"), Catcode.LETTER)
    return []


def make_at_other_handler(
    expander: ExpanderCore, node: CommandNode
) -> Optional[List[ASTNode]]:
    expander.set_catcode(ord("@"), Catcode.OTHER)
    return []


def register_makeat(expander: ExpanderCore):
    expander.register_handler("\\makeatletter", make_at_letter_handler, is_global=True)
    expander.register_handler("\\makeatother", make_at_other_handler, is_global=True)
