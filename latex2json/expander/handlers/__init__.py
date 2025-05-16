from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.primitives import register_primitives


def register_handlers(expander: ExpanderCore):
    register_primitives(expander)
