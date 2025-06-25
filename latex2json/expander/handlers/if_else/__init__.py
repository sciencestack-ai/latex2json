from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.if_else.base_if import register_base_ifs
from latex2json.expander.handlers.if_else.ifcase import register_ifcase
from latex2json.expander.handlers.if_else.ifcat import register_ifcat
from latex2json.expander.handlers.if_else.ifdim import register_ifdim
from latex2json.expander.handlers.if_else.ifnum import register_ifnum
from latex2json.expander.handlers.if_else.at_ifs import register_atifs
from latex2json.expander.handlers.if_else.ifthenelse import register_ifthenelse
from latex2json.expander.handlers.if_else.ifx import register_ifx
from latex2json.expander.handlers.if_else.newif import register_newif
from latex2json.expander.handlers.if_else.iffileexists import register_iffileexists


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
