from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.text_transforms.case_handlers import (
    register_case_handlers,
)


def register_text_transforms(expander: ExpanderCore):
    register_case_handlers(expander)
