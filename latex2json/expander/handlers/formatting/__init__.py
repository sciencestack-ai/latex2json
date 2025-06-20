from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.formatting.ignore_formatting_handlers import (
    register_ignore_format_handlers,
)
from latex2json.expander.handlers.formatting.number_format_handler import (
    register_number_format_handlers,
)
from latex2json.expander.handlers.formatting.layout_content_handlers import (
    register_layout_content_handlers,
)


def register_formatting_handlers(expander: ExpanderCore):
    register_ignore_format_handlers(expander)
    register_number_format_handlers(expander)
    register_layout_content_handlers(expander)
