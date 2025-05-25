from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.environment.environments import (
    register_base_environment_handlers,
)


def register_environment_handlers(expander: ExpanderCore):
    register_base_environment_handlers(expander)
