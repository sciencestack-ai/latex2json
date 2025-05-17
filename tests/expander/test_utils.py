from typing import List
import pytest

from latex2json.nodes import ArgNode, TextNode
from latex2json.expander.handlers.utils import substitute_args
from latex2json.nodes.base import ASTNode
from tests.test_utils import assert_ast_sequence


def test_substitute_args():

    argnode_d1_ind1 = ArgNode(1, 1)
    argnode_d1_ind2 = ArgNode(2, 1)
    argnode_d2_ind1 = ArgNode(1, 2)

    # e.g. #1 x #2 = ##1
    definition: List[ASTNode] = [
        argnode_d1_ind1,
        TextNode(" x "),
        argnode_d1_ind2,
        TextNode(" = "),
        argnode_d2_ind1,
    ]

    # normally, in a macro expansion, the first level of arguments is expanded first
    depth1_args = [TextNode("100"), TextNode("2")]
    substitute_args(definition, depth1_args, depth=argnode_d1_ind1.depth)
    assert argnode_d1_ind1.value == [TextNode("100")]
    assert argnode_d1_ind2.value == [TextNode("2")]

    # then the next level of arguments is expanded
    depth2_args = [TextNode("200")]
    substituted = substitute_args(definition, depth2_args, depth=argnode_d2_ind1.depth)
    assert argnode_d2_ind1.value == [TextNode("200")]
    assert_ast_sequence(
        substituted,
        [
            TextNode("100"),
            TextNode(" x "),
            TextNode("2"),
            TextNode(" = "),
            TextNode("200"),
        ],
    )
