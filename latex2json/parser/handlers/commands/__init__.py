from latex2json.parser.parser_core import ParserCore

from latex2json.parser.handlers.commands.doc_content_handler import (
    register_doc_content_handlers,
)
from latex2json.parser.handlers.commands.footnote_bookmark_handlers import (
    register_footnote_bookmark_handlers,
)
from latex2json.parser.handlers.commands.includegraphics_pdf_handlers import (
    register_includegraphics_pdf_handlers,
)
from latex2json.parser.handlers.commands.tabular_cell_handlers import (
    register_tabular_cell_handlers,
)
from latex2json.parser.handlers.commands.ref_cite_label_handlers import (
    register_ref_label_handlers,
)
from latex2json.parser.handlers.commands.text_handlers import register_text_handlers
from latex2json.parser.handlers.commands.highlight_handlers import (
    register_highlight_handlers,
)
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
from latex2json.parser.handlers.commands.frac_handlers import register_frac_handlers
from latex2json.parser.handlers.commands.symbol_handler import (
    register_symbol_handler,
)


def register_command_handlers(parser: ParserCore):
    # register generic latex2unicode first so that others below can override
    register_latex2unicode_handler(parser)
    register_diacritics_handler(parser)
    register_text_handlers(parser)
    register_highlight_handlers(parser)
    register_ref_label_handlers(parser)
    register_tabular_cell_handlers(parser)
    register_footnote_bookmark_handlers(parser)
    register_includegraphics_pdf_handlers(parser)
    register_doc_content_handlers(parser)
    register_spacing_handlers(parser)
    register_box_handlers(parser)
    register_frac_handlers(parser)
    register_symbol_handler(parser)
