from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.primitives.makeat import register_makeat
from latex2json.expander.handlers.primitives.bgroup import register_bgroup
from latex2json.expander.handlers.primitives.catcode import register_catcode


def register_primitives(expander: ExpanderCore):
    register_makeat(expander)
    register_bgroup(expander)
    register_catcode(expander)
