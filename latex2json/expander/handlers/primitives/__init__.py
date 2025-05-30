from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.primitives.begin_end import register_begin_end
from latex2json.expander.handlers.primitives.csname import register_csname_handlers
from latex2json.expander.handlers.primitives.declarations import register_declarations
from latex2json.expander.handlers.primitives.expand_handlers import (
    register_expand_handlers,
)
from latex2json.expander.handlers.primitives.makeat import register_makeat
from latex2json.expander.handlers.primitives.bgroup import register_bgroup
from latex2json.expander.handlers.primitives.catcode import register_catcode
from latex2json.expander.handlers.primitives.debug_handlers import (
    register_debug_handlers,
)


def register_primitives(expander: ExpanderCore):
    register_declarations(expander)
    register_makeat(expander)
    register_bgroup(expander)
    register_catcode(expander)
    register_begin_end(expander)
    register_debug_handlers(expander)
    register_expand_handlers(expander)
    register_csname_handlers(expander)
