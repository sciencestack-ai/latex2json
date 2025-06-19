from latex2json.parser.handlers.environments.list_handlers import register_list_handlers
from latex2json.parser.parser_core import ParserCore
from latex2json.parser.handlers.environments.tabular_handler import (
    register_tabular_handlers,
)
from latex2json.parser.handlers.environments.math_env_handlers import (
    register_math_env_handlers,
)
from latex2json.parser.handlers.environments.subfloat_handler import (
    register_subfloat_handler,
)


def register_env_handlers(parser: ParserCore):
    register_tabular_handlers(parser)
    register_math_env_handlers(parser)
    register_list_handlers(parser)
    register_subfloat_handler(parser)
