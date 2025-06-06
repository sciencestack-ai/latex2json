from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util


def register_fam_handlers(expander: ExpanderCore):

    ignore_patterns = {
        r"\newfam": "\\",  # e.g. \newfam\fontfam
        r"\textfont": "\\=\\",  # e.g. \textfont\fontfam=\xxxx
        r"\scriptfont": "\\=\\",
        r"\scriptscriptfont": "\\=\\",
    }
    register_ignore_handlers_util(expander, ignore_patterns)
