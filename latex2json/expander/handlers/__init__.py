from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.environment import (
    register_environment_handlers,
)
from latex2json.expander.handlers.for_loops import register_for_loop_handlers
from latex2json.expander.handlers.if_else import register_if_else
from latex2json.expander.handlers.inputs import register_input_handlers
from latex2json.expander.handlers.primitives import register_primitives
from latex2json.expander.handlers.registers import register_register_handlers
from latex2json.expander.handlers.sectioning import register_sectioning_handlers
from latex2json.expander.handlers.text_and_fonts import register_text_and_font_handlers


def register_handlers(expander: ExpanderCore):
    register_primitives(expander)
    register_if_else(expander)
    register_register_handlers(expander)
    register_text_and_font_handlers(expander)
    register_sectioning_handlers(expander)
    register_environment_handlers(expander)
    register_input_handlers(expander)
    register_for_loop_handlers(expander)
