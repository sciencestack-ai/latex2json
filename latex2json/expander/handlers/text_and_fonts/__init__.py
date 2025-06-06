from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.text_and_fonts.case_handlers import (
    register_case_handlers,
)
from latex2json.expander.handlers.text_and_fonts.color_handlers import (
    register_color_handlers,
)
from latex2json.expander.handlers.text_and_fonts.fam_handlers import (
    register_fam_handlers,
)
from latex2json.expander.handlers.text_and_fonts.font_handlers import (
    register_font_handlers,
)


def register_text_and_font_handlers(expander: ExpanderCore):
    register_case_handlers(expander)
    register_font_handlers(expander)
    register_color_handlers(expander)
    register_fam_handlers(expander)
