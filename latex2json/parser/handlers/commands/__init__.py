from latex2json.parser.handlers.commands.doc_content_handler import (
    register_doc_content_handlers,
)
from latex2json.parser.handlers.commands.footnote_bookmark_handlers import (
    register_footnote_bookmark_handlers,
)
from latex2json.parser.handlers.commands.ignore_format_handlers import (
    register_ignore_format_handlers,
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
from latex2json.parser.handlers.commands.spacing_handlers import (
    register_spacing_handlers,
)
from latex2json.parser.handlers.commands.latex2unicode_handler import (
    register_latex2unicode_handler,
)
from latex2json.parser.handlers.commands.diacritics_handler import (
    register_diacritics_handler,
)
from latex2json.parser.handlers.commands.box_handlers import register_box_handlers


def register_command_handlers(parser: ParserCore):
    # register generic latex2unicode first so that others below can override
    register_latex2unicode_handler(parser)
    register_diacritics_handler(parser)
    register_text_handlers(parser)
    register_ref_label_handlers(parser)
    register_multicol_row_handlers(parser)
    register_makecell_shortstack_handlers(parser)
    register_footnote_bookmark_handlers(parser)
    register_includegraphics_pdf_handlers(parser)
    register_ignore_format_handlers(parser)
    register_doc_content_handlers(parser)
    register_spacing_handlers(parser)
    register_box_handlers(parser)
