from latex2json.parser.parser_core import ParserCore
from latex2json.parser.handlers.bibliography.bibitem_handler import (
    register_bibitem_handler,
)
from latex2json.parser.handlers.bibliography.bibdiv_handler import (
    register_bibdiv_handler,
)


def register_all_bibliography_handlers(parser: ParserCore):
    register_bibitem_handler(parser)
    register_bibdiv_handler(parser)
