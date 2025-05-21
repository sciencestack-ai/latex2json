from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.registers.advance_handler import (
    register_advance_handler,
)


def register_register_handlers(expander: ExpanderCore):
    register_advance_handler(expander)
