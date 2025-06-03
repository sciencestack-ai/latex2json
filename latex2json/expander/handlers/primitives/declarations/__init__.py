from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.primitives.declarations.declare_handler import (
    register_declare_commands,
)
from latex2json.expander.handlers.primitives.declarations.let_handler import (
    register_let,
)
from latex2json.expander.handlers.primitives.declarations.namedef_handler import (
    register_namedef,
)
from latex2json.expander.handlers.primitives.declarations.newcommand import (
    register_newcommand,
)
from latex2json.expander.handlers.primitives.declarations.def_handler import (
    register_def,
)


def register_declarations(expander: ExpanderCore):

    register_def(expander)
    register_let(expander)
    register_newcommand(expander)
    register_declare_commands(expander)
    register_namedef(expander)
