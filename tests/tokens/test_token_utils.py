from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.utils import substitute_token_args
from tests.test_utils import assert_token_sequence


def test_substitute_token_args():
    def test1():
        # suppose definition ie e.g. "a 1 #1c #22##1"
        definition = [
            Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.PARAMETER, "1"),
            Token(TokenType.CHARACTER, "c", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.PARAMETER, "2"),
            Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
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
        substituted = substitute_token_args(definition, args)

        expected = [
            Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            *arg1,
            Token(TokenType.CHARACTER, "c", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            *arg2,
            Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
        ]
        assert_token_sequence(substituted, expected)

        # # now lets test second by giving empty arg
        # substituted = substitute_token_args(
        #     substituted, [[]], depth=ArgNode.compute_depth(num_params=2)
        # )
        # expected = [
        #     Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
        #     Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        #     Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
        #     Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        #     *arg1,
        #     Token(TokenType.CHARACTER, "c", catcode=Catcode.LETTER),
        #     Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        #     *arg2,
        #     Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
        # ]
        # assert_token_sequence(substituted, expected)

    test1()

    def test2():
        # test args in diff order
        # usage: #2#1
        definition = [
            Token(TokenType.PARAMETER, "2"),
            Token(TokenType.PARAMETER, "1"),
        ]
        arg1 = [
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "3", catcode=Catcode.OTHER),
        ]
        arg2 = [
            Token(TokenType.CHARACTER, "4", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "5", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "6", catcode=Catcode.OTHER),
        ]
        args = [arg1, arg2]
        substituted = substitute_token_args(definition, args)

        expected = [*arg2, *arg1]
        assert_token_sequence(substituted, expected)

    test2()
