from typing import Dict, List
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


def find_all_inner_tabular_tokens(tokens: List[Token]) -> List[tuple[int, int]]:
    """Find all inner environment token ranges, accounting for nesting.

    Args:
        tokens: List of tokens to search through

    Returns:
        List of (start_index, end_index) tuples for all inner environment tokens,
        in order of appearance.
    """
    stack = []
    matches = []

    for i, tok in enumerate(tokens):
        if tok.type == TokenType.ENVIRONMENT_START and tok.value in TABULAR_ENV_NAMES:
            stack.append((i, tok.value))
        elif tok.type == TokenType.ENVIRONMENT_END and tok.value in TABULAR_ENV_NAMES:
            if not stack:
                continue

            start_idx, env_name = stack[-1]
            if tok.value == env_name:
                stack.pop()
                # If stack is empty, we found a complete environment
                if not stack:
                    matches.append((start_idx, i))

    return matches


SubstituteMapType = Dict[str, List[ASTNode]]


def process_inner_tabular_environments(
    parser: ParserCore, tokens: List[Token]
) -> tuple[List[Token], SubstituteMapType]:
    """Process inner tabular environments by replacing them with mock control sequence tokens.

    Args:
        parser: The parser instance
        tokens: List of tokens to process

    Returns:
        Tuple of (processed tokens, mapping of mock names to tabular nodes)
    """
    substitute_map: SubstituteMapType = {}
    inner_envs = find_all_inner_tabular_tokens(tokens)

    if not inner_envs:
        return tokens, substitute_map

    final_tokens: List[Token] = []
    last_idx = 0
    for start_idx, end_idx in inner_envs:
        final_tokens.extend(tokens[last_idx:start_idx])
        last_idx = end_idx + 1

        tab_start_token = tokens[start_idx]
        parser.push_tokens(tokens[start_idx + 1 : end_idx + 1])
        out = tabular_handler(parser, tab_start_token)
        if out:
            # Create a mock substitute token to replace the original tabular environment
            mock_name = f"<tabularsub>{len(substitute_map)}</tabularsub>"
            substitute_map[mock_name] = out
            final_tokens.append(Token(TokenType.CONTROL_SEQUENCE, mock_name))

    final_tokens.extend(tokens[last_idx:])
    return final_tokens, substitute_map


def process_table_tokens_to_nodes(
    parser: ParserCore,
    table_tokens: List[List[List[Token]]],
    strip_null_rows: bool = True,
    substitute_map: SubstituteMapType = {},
) -> List[RowNode]:
    row_nodes: List[RowNode] = []
    for row_tokens in table_tokens:
        row_cells: List[CellNode] = []
        for col_tokens in row_tokens:
            col_nodes: List[ASTNode] = []
            N = len(col_tokens)
            last_idx = 0
            if len(substitute_map) > 0:
                for i, tok in enumerate(col_tokens):
                    if (
                        tok.type == TokenType.CONTROL_SEQUENCE
                        and tok.value in substitute_map
                    ):
                        col_nodes.extend(parser.process_tokens(col_tokens[last_idx:i]))
                        col_nodes.extend(substitute_map[tok.value])
                        last_idx = i + 1
            col_nodes.extend(parser.process_tokens(col_tokens[last_idx:N]))
            row_cells.append(merge_nodes_into_cellnode(col_nodes))
        row_nodes.append(RowNode(row_cells))

    if strip_null_rows:
        while row_nodes and row_nodes[0].is_null_row():
            row_nodes.pop(0)
        while row_nodes and row_nodes[-1].is_null_row():
            row_nodes.pop()

    return row_nodes


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

    # Handle all inner tabular environments
    final_tokens, substitute_map = process_inner_tabular_environments(parser, tokens)

    # Split into rows and columns
    rows = split_into_rows(final_tokens)
    table_tokens = [split_row_into_columns(row) for row in rows]  # row -> column

    row_nodes = process_table_tokens_to_nodes(
        parser,
        table_tokens,
        substitute_map=substitute_map,
        strip_null_rows=True,
    )
    return [TabularNode(row_nodes)]


TABULAR_ENV_NAMES = ["tabular", "longtable", "tabularx", "tabulary"]
TABULAR_ENV_NAMES.extend(name + "*" for name in TABULAR_ENV_NAMES[:])


def register_tabular_handlers(parser: ParserCore):
    for env_name in TABULAR_ENV_NAMES:
        parser.register_env_handler(env_name, tabular_handler)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
    \begin{tabular}{c}
        FIRST &
        \begin{tabular}{c}
            \begin{tabular}{c} 111 \end{tabular} \\ 22
        \end{tabular} \\
        44 & \begin{tabular}{c} 222 \end{tabular}
        & LAST
    \end{tabular}
    """.strip()
    # tokens = parser.expander.expand(text)
    out = parser.parse(text)
