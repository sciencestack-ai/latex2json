from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.primitives.begin_end import register_begin_end
from latex2json.expander.handlers.primitives.chardef_handlers import (
    register_chardef_handlers,
)
from latex2json.expander.handlers.primitives.csname import register_csname_handlers
from latex2json.expander.handlers.primitives.declarations import register_declarations
from latex2json.expander.handlers.primitives.expand_handlers import (
    register_expand_handlers,
)
from latex2json.expander.handlers.primitives.makeat import register_makeat
from latex2json.expander.handlers.primitives.bgroup_egroup import register_bgroup
from latex2json.expander.handlers.primitives.catcode_sfcode_handlers import (
    register_catcode_sfcode_handlers,
)
from latex2json.expander.handlers.primitives.debug_handlers import (
    register_debug_handlers,
)
from latex2json.expander.handlers.primitives.exec_handlers import register_exec_handlers
from latex2json.expander.handlers.primitives.addtomacro import (
    register_addtomacro_handler,
)
from latex2json.expander.handlers.primitives.dblarg import register_dblarg_handlers
from latex2json.expander.handlers.primitives.at_x_of_x import (
    register_at_x_of_x_handlers,
)


def register_primitives(expander: ExpanderCore):
    register_declarations(expander)
    register_makeat(expander)
    register_bgroup(expander)
    register_catcode_sfcode_handlers(expander)
    register_begin_end(expander)
    register_debug_handlers(expander)
    register_expand_handlers(expander)
    register_csname_handlers(expander)
    register_exec_handlers(expander)
    register_chardef_handlers(expander)
    register_addtomacro_handler(expander)
    register_dblarg_handlers(expander)
    register_at_x_of_x_handlers(expander)
