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
from latex2json.parser.handlers.environments.verbatim_lst_handlers import (
    register_verbatim_lst_handlers,
)
from latex2json.parser.handlers.environments.overpic_handler import (
    register_overpic_handler,
)
from latex2json.parser.handlers.environments.tikz_pgf_handlers import (
    register_tikz_pgf_handlers,
)


def register_env_handlers(parser: ParserCore):
    register_tabular_handlers(parser)
    register_math_env_handlers(parser)
    register_list_handlers(parser)
    register_subfloat_handler(parser)
    register_verbatim_lst_handlers(parser)
    register_overpic_handler(parser)
    register_tikz_pgf_handlers(parser)
