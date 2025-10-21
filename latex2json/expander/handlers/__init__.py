from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.environment import (
    register_environment_handlers,
)
from latex2json.expander.handlers.for_loops import register_all_loop_handlers
from latex2json.expander.handlers.formatting import register_formatting_handlers
from latex2json.expander.handlers.frontmatter import register_frontmatter_handlers
from latex2json.expander.handlers.handler_utils import make_math_command_handler
from latex2json.expander.handlers.if_else import register_if_else
from latex2json.expander.handlers.inputs import register_input_handlers
from latex2json.expander.handlers.primitives import register_primitives
from latex2json.expander.handlers.registers import register_register_handlers
from latex2json.expander.handlers.sectioning import register_sectioning_handlers
from latex2json.expander.handlers.text_and_fonts import register_text_and_font_handlers


from latex2json.latex_maps.math_commands import MATH_COMMANDS


def register_handlers(expander: ExpanderCore):
    register_formatting_handlers(
        expander
    )  # put formatting ignore first so that the others can override any aggressive ignore formatting
    register_register_handlers(expander)
    register_if_else(expander)
    register_primitives(expander)
    register_text_and_font_handlers(expander)
    register_sectioning_handlers(expander)
    register_environment_handlers(expander)
    register_input_handlers(expander)
    register_all_loop_handlers(expander)
    register_frontmatter_handlers(expander)

    """Wrap math commands with proper {} braces"""
    for command, argspec in MATH_COMMANDS.items():
        expander.register_handler(
            command, make_math_command_handler(command, argspec), is_global=True
        )
