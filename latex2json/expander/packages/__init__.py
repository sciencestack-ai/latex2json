from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.packages.cleveref import register_cleveref
from latex2json.expander.packages.epsfig import register_epsfig
from latex2json.expander.packages.tikz import register_tikz
from latex2json.expander.packages.keyval import register_keyval_handlers
from latex2json.expander.packages.thmtools import register_thmtools
from latex2json.expander.packages.tcolorbox import register_tcolorbox


def register_packages(expander: ExpanderCore):
    register_cleveref(expander)
    register_tikz(expander)
    register_keyval_handlers(expander)
    register_thmtools(expander)
    register_tcolorbox(expander)
    register_epsfig(expander)
