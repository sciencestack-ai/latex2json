from latex2json.nodes.tabular_node import CellNode
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens import Token
from latex2json.parser.handlers.environments.tabular_handler import split_into_rows
from latex2json.nodes.base_nodes import CommandNode


def makecell_handler(parser: ParserCore, token: Token):
    r"""Handle \makecell command which creates a cell with line breaks in tables.
    Format: \makecell[alignment]{content with \\ for line breaks}
    """
    parser.skip_whitespace()
    # Optional alignment parameter
    _ = parser.parse_bracket_as_nodes()
    parser.skip_whitespace()
    # Required content parameter
    content_nodes = parser.parse_brace_as_nodes(scoped=True)

    out_nodes = []
    if content_nodes:
        rows = split_into_rows(content_nodes)
        for row in rows:
            out_nodes.extend(strip_whitespace_nodes(row))
            out_nodes.append(CommandNode("newline"))

    return [CellNode(body=out_nodes)]


def register_makecell_shortstack_handlers(parser: ParserCore):
    parser.register_handler("makecell", makecell_handler)
    parser.register_handler("shortstack", makecell_handler)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
    \begin{tabular}{c}
        \begin{tabular}{c}
            \makecell{111 \\ 222}
        \end{tabular}
    \end{tabular}
    """.strip()
    # tokens = parser.expander.expand(text)
    out = parser.parse(text)
