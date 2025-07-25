from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.utils import (
    substitute_token_args,
    segment_tokens_by_begin_end_and_braces,
)
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


def test_segment_tokens_by_begin_end_and_braces():
    from latex2json.expander.expander import Expander

    expander = Expander()
    text = r"""
    \begin{xxx}\end{xxx} 
    sometext
    {aaa \\ bbb} 
    ccc
    {
    BRACE
    \begin{yyy}\end{yyy}
    }
    """.strip()
    tokens = expander.expand(text)
    groups = segment_tokens_by_begin_end_and_braces(tokens)

    expected_pairs = [
        (r"""\begin{xxx}\end{xxx}""", True),
        (r"""sometext""", False),
        (r"""{aaa\\bbb}""", True),
        (r"""ccc""", False),
        (r"""{BRACE\begin{yyy}\end{yyy}}""", True),
    ]

    assert len(groups) == len(expected_pairs)

    for i, (expected_str, expected_is_group) in enumerate(expected_pairs):
        tok_str = expander.convert_tokens_to_str(groups[i].tokens).strip()
        tok_str = tok_str.replace("\n", " ").replace(" ", "")
        assert tok_str == expected_str
        assert groups[i].is_group == expected_is_group
