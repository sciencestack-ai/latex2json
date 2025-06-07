from latex2json.parser.parser_core import ParserCore
from latex2json.parser.handlers.commands.command_handler_utils import (
    register_ignore_handlers_util,
)


def register_ignore_format_handlers(parser: ParserCore):
    # bookmarks
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
        "rule": "{{",
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
