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
    # multirow/col
    parser.register_handler("multirow", multirow_handler)
    parser.register_handler("multicolumn", multicolumn_handler)

    # cellcolor
    parser.register_handler("cellcolor", cellcolor_handler)
    # diagbox
    parser.register_handler("diagbox", diagbox_handler)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
		\begin{tabular}{c|c|c|c|c|c|c|c|c}
			\Xhline{3\arrayrulewidth} \bigstrut
			  & \multicolumn{4}{c|}{Variance Exploding SDE (SMLD)} & \multicolumn{4}{c}{Variance Preserving SDE (DDPM)}\\
			 \Xhline{1\arrayrulewidth}\bigstrut
			\diagbox[height=1cm, width=3cm]{Predictor}{FID$\downarrow$}{Sampler} & P1000 & \cellcolor{h}P2000 & \cellcolor{h}C2000 & \cellcolor{h}PC1000 & P1000 & \cellcolor{h}P2000 & \cellcolor{h}C2000 & \cellcolor{h}PC1000  \\
			\Xhline{1\arrayrulewidth}\bigstrut
            ancestral sampling & 4.98\scalebox{0.7}{ $\pm$ .06}	& \cellcolor{h}4.88\scalebox{0.7}{ $\pm$ .06} &\cellcolor{h} & \cellcolor{h}\textbf{3.62\scalebox{0.7}{ $\pm$ .03}} & 3.24\scalebox{0.7}{ $\pm$ .02}	& \cellcolor{h}3.24\scalebox{0.7}{ $\pm$ .02} &\cellcolor{h} & \cellcolor{h}\textbf{3.21\scalebox{0.7}{ $\pm$ .02}}\\
        	reverse diffusion & 4.79\scalebox{0.7}{ $\pm$ .07} & \cellcolor{h}4.74\scalebox{0.7}{ $\pm$ .08} & \cellcolor{h} & \cellcolor{h}\textbf{3.60\scalebox{0.7}{ $\pm$ .02}} & 3.21\scalebox{0.7}{ $\pm$ .02} & \cellcolor{h}3.19\scalebox{0.7}{ $\pm$ .02} & \cellcolor{h} &\cellcolor{h}\textbf{3.18\scalebox{0.7}{ $\pm$ .01}}\\
            probability flow &	15.41\scalebox{0.7}{ $\pm$ .15} &\cellcolor{h}10.54\scalebox{0.7}{ $\pm$ .08}&\cellcolor{h} \multirow{-3}{*}{20.43\scalebox{0.7}{ $\pm$ .07}} & \cellcolor{h}\textbf{3.51\scalebox{0.7}{ $\pm$ .04}} & 3.59\scalebox{0.7}{ $\pm$ .04} & \cellcolor{h}3.23\scalebox{0.7}{ $\pm$ .03} & \cellcolor{h}\multirow{-3}{*}{19.06\scalebox{0.7}{ $\pm$ .06}} & \cellcolor{h}\textbf{3.06\scalebox{0.7}{ $\pm$ .03}}\\
			\Xhline{3\arrayrulewidth}
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
