from typing import Optional, Tuple, List

from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token
from latex2json.nodes.base_nodes import ASTNode, TextNode
from latex2json.nodes.tabular_node import CellNode


def _parse_number_and_nodes(parser: ParserCore) -> Optional[Tuple[List[ASTNode], int]]:
    parser.skip_whitespace()
    brace1 = parser.parse_brace_as_nodes()

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
    parser.parse_brace_as_nodes()

    # 3rd arg is the content
    parser.skip_whitespace()
    nodes = parser.parse_brace_as_nodes()
    return nodes or [], number


def multirow_handler(parser: ParserCore, token: Token):
    parsed = _parse_number_and_nodes(parser)
    if not parsed:
        return []

    nodes, num_rows = parsed
    return [CellNode(body=nodes or [], rowspan=num_rows)]


def multicolumn_handler(parser: ParserCore, token: Token):
    parsed = _parse_number_and_nodes(parser)
    if not parsed:
        return []

    nodes, num_cols = parsed
    # check if internally has CellNode i.e. multirow
    out_nodes: List[ASTNode] = []

    max_rows = 1
    for node in nodes:
        if isinstance(node, CellNode):
            out_nodes.extend(node.body)
            max_rows = max(max_rows, node.rowspan)
        else:
            out_nodes.append(node)

    return [CellNode(body=out_nodes, colspan=num_cols, rowspan=max_rows)]


def register_multicol_row_handlers(parser: ParserCore):
    parser.register_handler("multirow", multirow_handler)
    parser.register_handler("multicolumn", multicolumn_handler)
