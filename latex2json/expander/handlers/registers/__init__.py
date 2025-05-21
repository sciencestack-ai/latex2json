from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.registers.count_handlers import (
    register_count_handlers,
)
from latex2json.expander.handlers.registers.dimen_handlers import (
    register_dimen_handlers,
)


def register_register_handlers(expander: ExpanderCore):
    register_count_handlers(expander)
    register_dimen_handlers(expander)
