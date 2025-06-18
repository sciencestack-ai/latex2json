from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.formatting.ignore_formatting_handlers import (
    register_ignore_format_handlers,
)
from latex2json.expander.handlers.formatting.number_format_handler import (
    register_number_format_handlers,
)
from latex2json.expander.handlers.formatting.spacing_handlers import (
    register_spacing_handlers,
)


def register_formatting_handlers(expander: ExpanderCore):
    register_ignore_format_handlers(expander)
    register_number_format_handlers(expander)
    register_spacing_handlers(expander)
