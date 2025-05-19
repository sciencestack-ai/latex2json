from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.if_else.ifx import register_ifx


def register_if_else(expander: ExpanderCore):
    register_ifx(expander)
