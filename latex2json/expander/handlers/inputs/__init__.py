from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.inputs.input_handler import (
    register_file_input_handlers,
)


def register_input_handlers(expander: ExpanderCore):
    register_file_input_handlers(expander)
