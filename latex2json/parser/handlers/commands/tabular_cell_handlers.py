from typing import Optional, Tuple, List

from latex2json.parser.handlers.commands.command_handler_utils import (
    register_ignore_handlers_util,
)
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens import Token
from latex2json.nodes import CommandNode, ASTNode, TextNode, CellNode
from latex2json.nodes.utils import split_nodes_into_rows, strip_whitespace_nodes


def merge_nodes_into_cellnode(
    nodes: List[ASTNode], strip_whitespace: bool = True, start_rows=1, start_cols=1
) -> CellNode:
    if strip_whitespace:
        nodes = strip_whitespace_nodes(nodes)

    # check if internally has CellNode i.e. multirow
    out_nodes: List[ASTNode] = []

    max_rows = start_rows
    max_cols = start_cols
    # check if nested cellnode from e.g. multirow

    cell_styles: List[str] = []
    for node in nodes:
        if isinstance(node, CellNode):
            out_nodes.extend(node.body)
            cell_styles.extend(node.styles)
            max_rows = max(max_rows, node.rowspan)
            max_cols = max(max_cols, node.colspan)
        else:
            out_nodes.append(node)

    cellnode = CellNode(body=out_nodes, rowspan=max_rows, colspan=max_cols)
    cellnode.add_styles(cell_styles, insert_at_front=True)
    return cellnode


def _parse_number_in_brace(parser: ParserCore, cmd_name: str) -> Optional[int]:
    parser.skip_whitespace()
    brace1 = parser.parse_brace_as_nodes(scoped=False)
    if not brace1 or not isinstance(brace1[0], TextNode):
        parser.logger.warning(
            f"{cmd_name}: expected a number as first argument, found {brace1} - defaulting to 1"
        )
        return 1
    try:
        number = int(brace1[0].text)
    except ValueError:
        parser.logger.warning(
            f"{cmd_name}: expected a number as first argument, found {brace1[0].text} - defaulting to 1"
        )
        return 1
    return number


def _parse_number_and_nodes(
    parser: ParserCore, cmd_name: str
) -> Optional[Tuple[List[ASTNode], int]]:
    number = _parse_number_in_brace(parser, cmd_name)

    # skip second arg
    parser.skip_whitespace()
    parser.parse_brace_as_nodes(scoped=False)

    # 3rd arg is the content
    parser.skip_whitespace()
    nodes = parser.parse_brace_as_nodes(scoped=True)
    return nodes or [], number


def multirow_handler(parser: ParserCore, token: Token):
    r"""\multirow[c]{2}{*}{...}"""
    parser.skip_whitespace()
    opt_arg1 = parser.parse_bracket_as_nodes()

    parsed = _parse_number_and_nodes(parser, token.value)
    if not parsed:
        return []

    nodes, num_rows = parsed
    cellnode = merge_nodes_into_cellnode(nodes, start_rows=num_rows)
    return [cellnode]


def multicolumn_handler(parser: ParserCore, token: Token):
    r"""\multicolumn{2}{c}{...}"""
    parsed = _parse_number_and_nodes(parser, token.value)
    if not parsed:
        return []

    nodes, num_cols = parsed

    cellnode = merge_nodes_into_cellnode(nodes, start_cols=num_cols)

    return [cellnode]


def multirowcell_handler(parser: ParserCore, token: Token):
    r"""
    multirowcell{2}[-0.5ex][l]{...}
    """
    number = _parse_number_in_brace(parser, token.value)

    parser.skip_whitespace()
    opt_arg1 = parser.parse_bracket_as_nodes()
    parser.skip_whitespace()
    opt_arg2 = parser.parse_bracket_as_nodes()
    parser.skip_whitespace()

    nodes = parser.parse_brace_as_nodes()
    return [merge_nodes_into_cellnode(nodes, start_rows=number)]


def makecell_handler(parser: ParserCore, token: Token):
    r"""Handle \makecell command which creates a cell with line breaks in tables.
    Format: \makecell[alignment]{content with \\ for line breaks}
    """
    parser.skip_whitespace()
    # Optional alignment parameter
    _ = parser.parse_bracket_as_nodes()
    parser.skip_whitespace()
    # Required content parameter
    content_nodes = parser.parse_brace_as_nodes(scoped=True) or []

    cellnode = merge_nodes_into_cellnode(content_nodes)
    if cellnode.body:
        # break the body into rows as \newline
        parsed_body = []
        rows = split_nodes_into_rows(cellnode.body)
        for row in rows:
            parsed_body.extend(strip_whitespace_nodes(row))
            parsed_body.append(CommandNode("newline"))

        cellnode.set_body(parsed_body)
    return [cellnode]


def cellcolor_handler(parser: ParserCore, token: Token):
    color_name = parser.parse_color_name()
    if not color_name:
        parser.logger.warning("\\cellcolor expects a color name")
        return []

    # create empty cellnode with style
    cellnode = CellNode(body=[])
    cellnode.add_styles(["color=" + color_name])

    return [cellnode]


def diagbox_handler(parser: ParserCore, token: Token):
    r"""
    Creates diagonal box cell in tabular
    \diagbox[height=1cm, width=3cm]{Predictor}{$r$}{Sampler}

    Just mock and split as .../.../..."""
    parser.skip_whitespace()
    parser.parse_bracket_as_nodes()
    parser.skip_whitespace()
    blocks = parser.parse_braced_blocks(3)
    if blocks:
        out_blocks = []
        for i, block in enumerate(blocks):
            out_blocks.extend(block)
            if i < len(blocks) - 1:
                out_blocks.append(TextNode(" / "))
        return out_blocks
    return []


def register_tabular_cell_handlers(parser: ParserCore):
    # makecell/shortstack
    parser.register_handler("makecell", makecell_handler)
    parser.register_handler("shortstack", makecell_handler)
    # thead is a wrapper around makecell
    parser.register_handler("thead", makecell_handler)

    # multirow/col
    parser.register_handler("multirowcell", multirowcell_handler)
    parser.register_handler("multirow", multirow_handler)
    parser.register_handler("multicolumn", multicolumn_handler)

    # cellcolor
    parser.register_handler("cellcolor", cellcolor_handler)
    # diagbox
    parser.register_handler("diagbox", diagbox_handler)

    ignore_patterns = {
        "theadfont": 1,
    }
    register_ignore_handlers_util(parser, ignore_patterns)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
		\begin{tabular}{c|c|c|c|c|c|c|c|c}
    \multirowcell{2}[-0.5ex]{
    LTF~\cite{kashyap2022transfuser}}

		\end{tabular}
    """.strip()

    #     text = r"""
    # \newcommand{\mjf}{$\mathcal{J}\&\mathcal{F}$\xspace}
    # \mjf
    # """

    out = parser.parse(text, postprocess=True)
    out = strip_whitespace_nodes(out)
    print(out)
    j = out[0].to_json()
