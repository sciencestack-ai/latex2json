from latex2json.nodes import FootnoteNode
from latex2json.nodes.base_nodes import TextNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token
from latex2json.parser.handlers.commands.command_handler_utils import (
    register_ignore_handlers_util,
)


def footnote_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    title_nodes = parser.parse_bracket_as_nodes()
    title = parser.convert_nodes_to_str(title_nodes) if title_nodes else None
    parser.skip_whitespace()
    content = parser.parse_brace_as_nodes()
    if content is None:
        parser.logger.warning(f"\\footnote: Missing content")
        return None
    return [FootnoteNode(content, title)]


def footnotemark_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    nodes = parser.parse_bracket_as_nodes() or [TextNode("*")]
    return []  # TODO?
    # return [FootnoteNode(nodes)]


def register_footnote_bookmark_handlers(parser: ParserCore):
    for footnote_command in ["footnote", "footnotetext"]:
        parser.register_handler(footnote_command, footnote_handler)
    parser.register_handler("footnotemark", footnotemark_handler)

    # bookmarks
    ignore_patterns = {
        "pdfbookmark": "[{{",
        "belowpdfbookmark": "[{{",
        "currentpdfbookmark": "[{{",
        "bookmark": "[{",
    }

    register_ignore_handlers_util(parser, ignore_patterns)


if __name__ == "__main__":
    from latex2json.parser.parser import Parser

    parser = Parser()
    register_footnote_bookmark_handlers(parser)

    text = r"""
    \pdfbookmark[1]{My bookmark}{my:bookmark}
    \belowpdfbookmark[1]{My bookmark}{my:bookmark}
    \currentpdfbookmark[1]{My bookmark}{my:bookmark}
    \bookmark[1]{My bookmark}
    """

    out = parser.parse(text)
    print(out)
