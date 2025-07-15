from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.packages.cleveref import register_cleveref
from latex2json.expander.packages.tikz import register_tikz


def register_packages(expander: ExpanderCore):
    register_cleveref(expander)
    register_tikz(expander)
