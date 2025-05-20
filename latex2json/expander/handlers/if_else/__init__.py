from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.if_else.base_if import register_base_ifs
from latex2json.expander.handlers.if_else.ifcat import register_ifcat
from latex2json.expander.handlers.if_else.ifx import register_ifx


def register_if_else(expander: ExpanderCore):
    register_base_ifs(expander)
    register_ifx(expander)
    register_ifcat(expander)
