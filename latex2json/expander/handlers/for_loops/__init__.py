from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.for_loops.for_each_handler import (
    register_for_each_handlers,
)


def register_for_loop_handlers(expander: ExpanderCore):
    register_for_each_handlers(expander)
