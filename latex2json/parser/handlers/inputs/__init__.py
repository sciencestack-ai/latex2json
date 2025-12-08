from latex2json.parser.parser_core import ParserCore

from latex2json.parser.handlers.inputs.subfile_handler import (
    register_externaldocument_handler,
)


def register_input_handlers(parser: ParserCore):
    register_externaldocument_handler(parser)
