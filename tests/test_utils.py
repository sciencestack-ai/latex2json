from typing import List

from latex2json.nodes import ASTNode


def assert_ast_sequence(asts: List[ASTNode], expected_sequence: List[ASTNode]):
    assert len(asts) == len(expected_sequence)
    for ast, expected in zip(asts, expected_sequence):
        assert ast == expected
