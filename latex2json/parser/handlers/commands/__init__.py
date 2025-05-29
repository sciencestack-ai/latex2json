from latex2json.parser.parser_core import ParserCore

from latex2json.parser.handlers.commands.multicol_row import (
    register_multicol_row_handlers,
)
from latex2json.parser.handlers.commands.ref_label_handlers import (
    register_ref_label_handlers,
)
from latex2json.parser.handlers.commands.text_handlers import register_text_handlers


def register_command_handlers(parser: ParserCore):
    register_text_handlers(parser)
    register_ref_label_handlers(parser)
    register_multicol_row_handlers(parser)
