from latex2json.expander.expander_core import ExpanderCore
from latex2json.registers import RegisterType

from latex2json.expander.handlers.if_else.base_if import register_base_ifs
from latex2json.expander.handlers.if_else.ifcase import register_ifcase
from latex2json.expander.handlers.if_else.ifcat import register_ifcat
from latex2json.expander.handlers.if_else.ifdim import register_ifdim
from latex2json.expander.handlers.if_else.ifnum import register_ifnum
from latex2json.expander.handlers.if_else.at_ifs import register_atifs
from latex2json.expander.handlers.if_else.ifthenelse import register_ifthenelse
from latex2json.expander.handlers.if_else.ifx import register_ifx
from latex2json.expander.handlers.if_else.newif import (
    register_newif,
    register_newif_name_macros,
)
from latex2json.expander.handlers.if_else.iffileexists import register_iffileexists
from latex2json.expander.handlers.if_else.ifdefempty import register_ifdefempty
from latex2json.expander.handlers.if_else.ifvoid import register_ifvoid
from latex2json.expander.handlers.if_else.ifcsname import register_ifcsname
from latex2json.latex_maps.latex_ifs import LATEX_IFS


def register_if_else(expander: ExpanderCore):
    register_base_ifs(expander)
    register_ifx(expander)
    register_ifcat(expander)
    register_ifnum(expander)
    register_ifdim(expander)
    register_newif(expander)
    register_atifs(expander)
    register_ifthenelse(expander)
    register_ifcase(expander)
    register_iffileexists(expander)
    register_ifdefempty(expander)
    register_ifvoid(expander)
    register_ifcsname(expander)

    # Register predefined LaTeX conditionals
    for name, initial_value in LATEX_IFS.items():
        register_newif_name_macros(expander, name, is_user_defined=False)
        expander.set_register(
            RegisterType.BOOL, "if" + name, initial_value, is_global=True
        )
