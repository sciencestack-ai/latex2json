from typing import List

from latex2json.nodes import ASTNode
from latex2json.tokens.types import Token


def assert_token_sequence(tokens: List[Token], expected_sequence: List[Token]):
    assert len(tokens) == len(expected_sequence)
    for token, expected in zip(tokens, expected_sequence):
        assert token == expected


def assert_ast_sequence(asts: List[ASTNode], expected_sequence: List[ASTNode]):
    assert len(asts) == len(expected_sequence)
    for ast, expected in zip(asts, expected_sequence):
        assert ast == expected
