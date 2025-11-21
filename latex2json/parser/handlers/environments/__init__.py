from latex2json.parser.handlers.environments.list_handler import register_list_handler
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
from latex2json.parser.handlers.environments.verbatim_lst_handlers import (
    register_verbatim_lst_handlers,
)
from latex2json.parser.handlers.environments.diagram_handlers import (
    register_picture_handlers,
)
from latex2json.parser.handlers.environments.algorithm_handlers import (
    register_algorithm_handlers,
)
from latex2json.parser.handlers.environments.table_figure_handlers import (
    register_table_figure_handlers,
)


def register_env_handlers(parser: ParserCore):
    register_tabular_handlers(parser)
    register_math_env_handlers(parser)
    register_list_handler(parser)
    register_subfloat_handler(parser)
    register_verbatim_lst_handlers(parser)
    register_picture_handlers(parser)
    register_algorithm_handlers(parser)
    register_table_figure_handlers(parser)
