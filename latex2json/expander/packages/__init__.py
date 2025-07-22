from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.packages.cleveref import register_cleveref
from latex2json.expander.packages.tikz import register_tikz
from latex2json.expander.packages.keyval import register_keyval_handlers


def register_packages(expander: ExpanderCore):
    register_cleveref(expander)
    register_tikz(expander)
    register_keyval_handlers(expander)
