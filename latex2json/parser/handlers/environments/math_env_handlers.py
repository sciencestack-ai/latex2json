from latex2json.nodes.math_nodes import EquationNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token


def ensuremath_handler(parser: ParserCore, token: Token):
    nodes = parser.parse_brace_as_nodes()
    return [EquationNode(nodes)]


def register_math_env_handlers(parser: ParserCore):
    parser.register_handler("ensuremath", ensuremath_handler)
