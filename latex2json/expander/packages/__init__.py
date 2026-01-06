from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.packages.cleveref import register_cleveref
from latex2json.expander.packages.epsfig import register_epsfig
from latex2json.expander.packages.tikz_pgf import register_tikz_pgf_handlers
from latex2json.expander.packages.keyval import register_keyval_handlers
from latex2json.expander.packages.thmtools import register_thmtools
from latex2json.expander.packages.tcolorbox import register_tcolorbox
from latex2json.expander.packages.titling import register_titling
from latex2json.expander.packages.siunitx import register_siunitx
from latex2json.expander.packages.enumitem import register_enumitem
from latex2json.expander.packages.parcolumns import register_parcolumns
from latex2json.expander.packages.other_packages import register_other_packages
from latex2json.expander.packages.etoolbox import register_etoolbox_handler
from latex2json.expander.packages.xpatch import register_xpatch_handler
from latex2json.expander.packages.xparse import register_xparse
from latex2json.expander.packages.pgfmath import register_pgfmath
from latex2json.expander.packages.xstring import register_xstring_handler
from latex2json.expander.packages.etoc import register_etoc


def register_packages(expander: ExpanderCore):
    register_xparse(expander)
    register_cleveref(expander)
    register_tikz_pgf_handlers(expander)
    register_keyval_handlers(expander)
    register_thmtools(expander)
    register_tcolorbox(expander)
    register_epsfig(expander)
    register_titling(expander)
    register_siunitx(expander)
    register_enumitem(expander)
    register_parcolumns(expander)
    register_other_packages(expander)
    register_etoolbox_handler(expander)
    register_xpatch_handler(expander)
    register_pgfmath(expander)
    register_xstring_handler(expander)
    register_etoc(expander)
