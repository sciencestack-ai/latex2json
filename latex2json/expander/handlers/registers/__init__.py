from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.registers.advance_handler import (
    register_advance_handler,
)
from latex2json.expander.handlers.registers.base_register_handlers import (
    register_base_register_macros,
)
from latex2json.expander.handlers.registers.counter_handlers import (
    register_counter_handlers,
)
from latex2json.expander.handlers.registers.counter_format_handlers import (
    register_counter_format_handlers,
)


def register_register_handlers(expander: ExpanderCore):
    register_advance_handler(expander)
    register_base_register_macros(expander)
    register_counter_handlers(expander)
    register_counter_format_handlers(expander)
