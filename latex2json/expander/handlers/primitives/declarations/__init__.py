from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.primitives.declarations.declare_handler import (
    register_declare_commands,
)
from latex2json.expander.handlers.primitives.declarations.let_handler import (
    register_let,
)
from latex2json.expander.handlers.primitives.declarations.newcommand import (
    register_newcommand,
)
from latex2json.expander.handlers.primitives.declarations.def_handler import (
    register_def,
)
from latex2json.expander.handlers.primitives.declarations.newenvironment import (
    register_newenvironment,
)


def register_declarations(expander: ExpanderCore):

    register_def(expander)
    register_let(expander)
    register_newcommand(expander)
    register_newenvironment(expander)
    register_declare_commands(expander)
