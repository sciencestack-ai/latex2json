from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.environment.caption_handler import (
    register_caption_handler,
)
from latex2json.expander.handlers.environment.environment_handlers import (
    register_base_environment_handlers,
)
from latex2json.expander.handlers.environment.float_handler import (
    register_float_handler,
)


def register_environment_handlers(expander: ExpanderCore):
    register_base_environment_handlers(expander)
    register_caption_handler(expander)
    register_float_handler(expander)
