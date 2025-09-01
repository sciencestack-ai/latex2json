from typing import Optional, Tuple, List

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


def _parse_number_and_nodes(parser: ParserCore) -> Optional[Tuple[List[ASTNode], int]]:
    parser.skip_whitespace()
    brace1 = parser.parse_brace_as_nodes(scoped=False)

    if not brace1 or not isinstance(brace1[0], TextNode):
        parser.logger.warning("multirow: expected {number} as first argument")
        return None

    try:
        number = int(brace1[0].text)
    except ValueError:
        parser.logger.warning("multirow: expected {number} as first argument")
        return None

    # skip second arg
    parser.skip_whitespace()
    parser.parse_brace_as_nodes(scoped=False)

    # 3rd arg is the content
    parser.skip_whitespace()
    nodes = parser.parse_brace_as_nodes(scoped=True)
    return nodes or [], number


def multirow_handler(parser: ParserCore, token: Token):
    parsed = _parse_number_and_nodes(parser)
    if not parsed:
        return []

    nodes, num_rows = parsed
    cellnode = merge_nodes_into_cellnode(nodes, start_rows=num_rows)
    return [cellnode]


def multicolumn_handler(parser: ParserCore, token: Token):
    parsed = _parse_number_and_nodes(parser)
    if not parsed:
        return []

    nodes, num_cols = parsed

    cellnode = merge_nodes_into_cellnode(nodes, start_cols=num_cols)

    return [cellnode]


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


def register_tabular_cell_handlers(parser: ParserCore):
    # makecell/shortstack
    parser.register_handler("makecell", makecell_handler)
    parser.register_handler("shortstack", makecell_handler)
    # multirow/col
    parser.register_handler("multirow", multirow_handler)
    parser.register_handler("multicolumn", multicolumn_handler)

    # cellcolor
    parser.register_handler("cellcolor", cellcolor_handler)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
    \newcommand{\baseline}[1]{\cellcolor{lightgray}{#1}}
    \newcommand{\mjf}{$\mathcal{J}\&\mathcal{F}$\xspace}
    \def\x{$\times$}

    \begin{tabular}{cccccccc}
    \multicolumn{2}{c}{} & \multicolumn{4}{c}{{\footnotesize \mjf}} &  &\multicolumn{1}{c}{{\footnotesize mIoU}} \\
    \cmidrule(lr){3-6}\cmidrule(lr){8-8}
    Object Pointers & GRU & MOSE dev & SA-V val & LVOSv2 val & 9 zero-shot & speed & SA-23 \\
    \midrule
     & &  \textbf{73.1} & 64.5 & 67.0 & \textbf{70.9} & \textbf{1.00\x} &59.9 \\
     & \checkmark & 72.3 & 65.3 & 68.9 & 70.5 & 0.97\x & \textbf{60.0} \\
     \baseline{\checkmark} &  \baseline{} & 73.0 & \textbf{68.3} & \textbf{71.6} & 70.7  & \textbf{1.00\x} & 59.7 \\
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
