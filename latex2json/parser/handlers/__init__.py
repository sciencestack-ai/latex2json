from latex2json.parser.handlers.ref_label_handlers import register_ref_label_handlers
from latex2json.parser.handlers.text_handlers import register_text_handlers
from latex2json.parser.parser_core import ParserCore


def register_handlers(parser: ParserCore):
    register_text_handlers(parser)
    register_ref_label_handlers(parser)
