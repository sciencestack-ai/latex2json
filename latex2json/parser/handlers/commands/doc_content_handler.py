from latex2json.parser.parser_core import ParserCore
from latex2json.parser.handlers.commands.command_handler_utils import (
    register_ignore_handlers_util,
    make_generic_command_handler,
)


def register_doc_content_handlers(parser: ParserCore):
    parser.register_handler("abstract", make_generic_command_handler("abstract", "{"))
    parser.register_handler("title", make_generic_command_handler("title", "[{"))
