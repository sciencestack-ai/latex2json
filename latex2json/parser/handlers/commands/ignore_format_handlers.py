from typing import Callable
from latex2json.nodes.base_nodes import CommandNode
from latex2json.tokens import Token
from latex2json.parser.parser_core import MacroPattern, ParserCore
from latex2json.parser.handlers.commands.command_handler_utils import (
    register_ignore_handlers_util,
)


def register_ignore_separators(parser: ParserCore):
    separator_patterns = {
        "hline": 0,
        "vline": 0,
        "hrulefill": 0,
        "centerline": 0,
        "cline": "{",
        "topsep": 0,
        "parsep": 0,
        "partopsep": 0,
        "labelsep": "{",
        "midrule": "[",
        "toprule": "[",
        "bottomrule": "[",
        "cmidrule": "([{",
        "hdashline": "[",
        "cdashline": "{",
        "specialrule": "{{{",
        "addlinespace": "[",
        "rule": "[{{",
        "hrule": 0,
        "morecmidrules": 0,
        "fboxsep": "{",
        "Xhline": "{",
        "tabcolsep": 0,
        "colrule": 0,
        "noalign": 0,
        "endfirsthead": 0,
    }

    register_ignore_handlers_util(parser, separator_patterns)


def ignore_brace_handler(parser: ParserCore, token: Token):
    # check that command is not user defined. Dont skip if user-defined
    if parser.expander.check_macro_is_user_defined(token.value):
        return [CommandNode(token.value)]

    parser.skip_whitespace()
    body = parser.parse_brace_as_nodes()
    return []


def register_ignore_format_handlers(parser: ParserCore):
    register_ignore_separators(parser)

    # ignore patterns
    hy_at_pattern: Callable[[str], bool] = lambda name: name.startswith("Hy@")

    parser.register_pattern_handler(hy_at_pattern, ignore_brace_handler)
