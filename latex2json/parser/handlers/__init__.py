from latex2json.parser.parser_core import ParserCore
from latex2json.parser.handlers.commands import register_command_handlers
from latex2json.parser.handlers.environments import register_env_handlers
from latex2json.parser.handlers.bibliography import register_all_bibliography_handlers
from latex2json.parser.handlers.inputs import register_input_handlers
from latex2json.parser.handlers.patterns_to_ignore import register_patterns_to_ignore


def register_handlers(parser: ParserCore):
    register_command_handlers(parser)
    register_env_handlers(parser)
    register_all_bibliography_handlers(parser)
    register_input_handlers(parser)
    register_patterns_to_ignore(parser)
