from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.formatting.ignore_formatting_handlers import (
    register_ignore_format_handlers,
)


def register_formatting_handlers(expander: ExpanderCore):
    register_ignore_format_handlers(expander)
