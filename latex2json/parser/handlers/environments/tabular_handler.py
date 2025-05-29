from typing import List
from latex2json.nodes.tabular_node import CellNode, RowNode, TabularNode
from latex2json.tokens import Catcode, EnvironmentStartToken, Token, TokenType
from latex2json.nodes import ASTNode, EnvironmentNode

from latex2json.parser.parser_core import EnvHandler, ParserCore, TokenPredicate
from latex2json.tokens.utils import is_alignment_token, strip_whitespace_tokens


def is_newcol_token(tok: Token) -> bool:
    return is_alignment_token(tok)


def is_newrow_token(tok: Token) -> bool:
    return tok.type == TokenType.CONTROL_SEQUENCE and tok.value == "\\"


def split_into_rows(tokens: List[Token]) -> List[List[Token]]:
    rows: List[List[Token]] = []
    current_row: List[Token] = []

    for tok in tokens:
        if is_newrow_token(tok):
            if current_row:
                rows.append(current_row)
            current_row = []
        else:
            current_row.append(tok)

    if current_row:
        rows.append(current_row)

    return rows


def split_row_into_columns(row_tokens: List[Token]) -> List[List[Token]]:
    columns: List[List[Token]] = []
    current_col: List[Token] = []

    for tok in row_tokens:
        if is_newcol_token(tok):
            columns.append(current_col)
            current_col = []
        else:
            current_col.append(tok)

    if current_col:
        columns.append(current_col)

    return [strip_whitespace_tokens(col) for col in columns]


def merge_nodes_into_cellnode(nodes: List[ASTNode]) -> CellNode:
    all_nodes: List[ASTNode] = []

    max_rowspan = 1
    max_colspan = 1
    for node in nodes:
        if isinstance(node, CellNode):
            all_nodes.extend(node.body)
            max_rowspan = max(max_rowspan, node.rowspan)
            max_colspan = max(max_colspan, node.colspan)
        else:
            all_nodes.append(node)
    return CellNode(all_nodes, rowspan=max_rowspan, colspan=max_colspan)


def process_table_tokens_to_nodes(
    parser: ParserCore, table_tokens: List[List[Token]]
) -> List[RowNode]:
    rows: List[RowNode] = []
    for row_tokens in table_tokens:
        row_cells: List[CellNode] = []
        for col_tokens in row_tokens:
            col_nodes = parser.process_tokens(col_tokens)
            row_cells.append(merge_nodes_into_cellnode(col_nodes))
        rows.append(RowNode(row_cells))

    return rows


def tabular_handler(parser: ParserCore, token: EnvironmentStartToken) -> List[ASTNode]:
    env_name = token.name

    begin_predicate: TokenPredicate = (
        lambda tok: tok.type == TokenType.ENVIRONMENT_START and tok.value == env_name
    )
    end_predicate: TokenPredicate = (
        lambda tok: tok.type == TokenType.ENVIRONMENT_END and tok.value == env_name
    )

    tokens = parser.parse_begin_end_as_tokens(
        begin_predicate,
        end_predicate,
        check_first_token=False,
        include_begin_end_tokens=False,
    )

    if not tokens:
        return [TabularNode()]

    # Split into rows and columns
    rows = split_into_rows(tokens)
    table_tokens = [split_row_into_columns(row) for row in rows]  # row -> column

    row_nodes = process_table_tokens_to_nodes(parser, table_tokens)
    return [TabularNode(row_nodes)]


TABULAR_ENV_NAMES = ["tabular", "longtable", "tabularx", "tabulary"]


def register_tabular_handlers(parser: ParserCore):
    for env_name in TABULAR_ENV_NAMES:
        parser.register_env_handler(env_name, tabular_handler)
        parser.register_env_handler(env_name + "*", tabular_handler)
