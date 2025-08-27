from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.registers.advance_handler import (
    register_advance_handler,
)
from latex2json.expander.handlers.registers.base_register_handlers import (
    register_base_register_macros,
)
from latex2json.expander.handlers.registers.bool_handlers import register_bool_handlers
from latex2json.expander.handlers.registers.box_handlers import register_box_handlers
from latex2json.expander.handlers.registers.counter_handlers import (
    register_counter_handlers,
)
from latex2json.expander.handlers.registers.counter_format_handlers import (
    register_counter_format_handlers,
)
from latex2json.expander.handlers.registers.length_handlers import (
    register_length_handlers,
)
from latex2json.expander.handlers.registers.insert_handlers import (
    register_insert_handlers,
)
from latex2json.expander.handlers.registers.skip_handlers import register_skip_handlers


def register_register_handlers(expander: ExpanderCore):
    register_advance_handler(expander)
    register_base_register_macros(expander)
    register_counter_handlers(expander)
    register_counter_format_handlers(expander)
    register_length_handlers(expander)
    register_box_handlers(expander)
    register_skip_handlers(expander)
    register_bool_handlers(expander)
    register_insert_handlers(expander)
