from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.sectioning.sections import register_section_handlers


def register_sectioning_handlers(expander: ExpanderCore):
    register_section_handlers(expander)
