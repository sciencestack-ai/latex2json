from latex2json.parser.parser_core import ParserCore

from latex2json.parser.handlers.inputs.subfile_handler import register_subfile_handlers


def register_input_handlers(parser: ParserCore):
    register_subfile_handlers(parser)
