from typing import List
import pytest

from latex2json.nodes import ArgNode, TextNode
from latex2json.expander.handlers.utils import substitute_args, substitute_token_args
from latex2json.nodes.base import ASTNode
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from tests.test_utils import assert_ast_sequence, assert_token_sequence


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


def test_substitute_token_args():
    # suppose definition ie e.g. "a # 1 #1c #22##1"
    definition = [
        Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
        Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, "c", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
        Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
        Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
        Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
    ]

    # and we want to sub #1 and #2 with "123" and "4 5 6"
    arg1 = [
        Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, "3", catcode=Catcode.OTHER),
    ]
    arg2 = [
        Token(TokenType.CHARACTER, "4", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "5", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "6", catcode=Catcode.OTHER),
    ]
    args = [arg1, arg2]
    substituted = substitute_token_args(
        definition, args, depth=ArgNode.compute_depth(num_params=1)
    )

    expected = [
        Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        *arg1,
        Token(TokenType.CHARACTER, "c", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        *arg2,
        Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
        Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
        Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
    ]
    assert_token_sequence(substituted, expected)

    # now lets test second by giving empty arg
    substituted = substitute_token_args(
        substituted, [[]], depth=ArgNode.compute_depth(num_params=2)
    )
    expected = [
        Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        *arg1,
        Token(TokenType.CHARACTER, "c", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        *arg2,
        Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
    ]
    assert_token_sequence(substituted, expected)
