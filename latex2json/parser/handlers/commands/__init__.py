from latex2json.parser.handlers.commands.footnote_bookmark_handlers import (
    register_footnote_bookmark_handlers,
)
from latex2json.parser.handlers.commands.includegraphics_pdf_handlers import (
    register_includegraphics_pdf_handlers,
)
from latex2json.parser.handlers.commands.makecell_shortstack import (
    register_makecell_shortstack_handlers,
)
from latex2json.parser.parser_core import ParserCore

from latex2json.parser.handlers.commands.multicol_row import (
    register_multicol_row_handlers,
)
from latex2json.parser.handlers.commands.ref_cite_label_handlers import (
    register_ref_label_handlers,
)
from latex2json.parser.handlers.commands.text_handlers import register_text_handlers


def register_command_handlers(parser: ParserCore):
    register_text_handlers(parser)
    register_ref_label_handlers(parser)
    register_multicol_row_handlers(parser)
    register_makecell_shortstack_handlers(parser)
    register_footnote_bookmark_handlers(parser)
    register_includegraphics_pdf_handlers(parser)
