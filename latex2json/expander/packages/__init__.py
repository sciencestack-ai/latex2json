from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.packages.cleveref import register_cleveref


def register_packages(expander: ExpanderCore):
    register_cleveref(expander)
