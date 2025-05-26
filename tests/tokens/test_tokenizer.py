import pytest
from typing import List


from latex2json.tokens import Tokenizer, Token, TokenType, Catcode


@pytest.fixture
def tokenizer():
    return Tokenizer()


def assert_tokenizer_sequence(
    tokenizer: Tokenizer, text: str, expected_tokens: List[Token]
):
    tokenizer.set(text)
    for i, token in enumerate(expected_tokens):
        assert tokenizer.get_next_token() == token
    assert tokenizer.get_next_token() is None
    assert tokenizer.eof()


def test_tokenizer_basic():
    tokenizer = Tokenizer()
    text = r"\def\foo{bar}"

    expected_tokens = [
        Token(TokenType.CONTROL_SEQUENCE, "def", 0),
        Token(TokenType.CONTROL_SEQUENCE, "foo", 4),
        # simple brace token
        Token(TokenType.CHARACTER, "{", 8, Catcode.BEGIN_GROUP),
        Token(TokenType.CHARACTER, "b", 9, Catcode.LETTER),
        Token(TokenType.CHARACTER, "a", 10, Catcode.LETTER),
        Token(TokenType.CHARACTER, "r", 11, Catcode.LETTER),
        Token(TokenType.CHARACTER, "}", 12, Catcode.END_GROUP),
    ]

    assert_tokenizer_sequence(tokenizer, text, expected_tokens)


def test_tokenizer_comment():
    tokenizer = Tokenizer()
    text = r"""
bar % comment
[baz]
    """.strip()

    line1_len = len(r"bar % comment")
    expected_tokens = [
        Token(TokenType.CHARACTER, "b", 0, Catcode.LETTER),
        Token(TokenType.CHARACTER, "a", 1, Catcode.LETTER),
        Token(TokenType.CHARACTER, "r", 2, Catcode.LETTER),
        Token(TokenType.CHARACTER, " ", 3, Catcode.SPACE),
        # skip comments?
        Token(TokenType.END_OF_LINE, "\n", line1_len),
        Token(TokenType.CHARACTER, "[", line1_len + 1, Catcode.OTHER),
        Token(TokenType.CHARACTER, "b", line1_len + 2, Catcode.LETTER),
        Token(TokenType.CHARACTER, "a", line1_len + 3, Catcode.LETTER),
        Token(TokenType.CHARACTER, "z", line1_len + 4, Catcode.LETTER),
        Token(TokenType.CHARACTER, "]", line1_len + 5, Catcode.OTHER),
        # Token(TokenType.END_OF_LINE, "\n", line1_len + 4),
    ]
    assert_tokenizer_sequence(tokenizer, text, expected_tokens)


def test_simulate_makeatletter():
    tokenizer = Tokenizer()

    # normally @ is OTHER
    text = r"@\@e"  # here \@ is its own control sequence since @ is distinct (OTHER) from e (LETTER)
    expected_tokens1 = [
        Token(TokenType.CHARACTER, "@", 0, Catcode.OTHER),
        Token(TokenType.CONTROL_SEQUENCE, "@", 1),
        Token(TokenType.CHARACTER, "e", 3, Catcode.LETTER),
    ]
    assert_tokenizer_sequence(tokenizer, text, expected_tokens1)

    # now make @ a LETTER
    tokenizer.set_catcode(ord("@"), Catcode.LETTER)
    # here, \@e becomes a single control sequence since @ is now LETTER
    expected_tokens2 = [
        Token(TokenType.CHARACTER, "@", 0, Catcode.LETTER),
        Token(TokenType.CONTROL_SEQUENCE, "@e", 1),
    ]
    assert_tokenizer_sequence(tokenizer, text, expected_tokens2)


def test_ignored_catcode():
    tokenizer = Tokenizer()
    # normally this is catcode.parameter
    text = "#3"
    expected_tokens = [
        Token(TokenType.CHARACTER, "#", 0, Catcode.PARAMETER),
        Token(TokenType.CHARACTER, "3", 1, Catcode.OTHER),
    ]
    assert_tokenizer_sequence(tokenizer, text, expected_tokens)

    # now make it ignored
    tokenizer.set_catcode(ord("#"), Catcode.IGNORED)
    # now #3 is just 3 since # is ignored
    expected_tokens2 = [
        Token(TokenType.CHARACTER, "3", 1, Catcode.OTHER),
    ]
    assert_tokenizer_sequence(tokenizer, text, expected_tokens2)

    # test with control sequence, \# -> \ since # is ignored
    text = r"\#3"
    expected_tokens = [
        Token(TokenType.CONTROL_SEQUENCE, r"", 0),
        Token(TokenType.CHARACTER, "3", 2, Catcode.OTHER),
    ]
    assert_tokenizer_sequence(tokenizer, text, expected_tokens)


def test_math():
    tokenizer = Tokenizer()
    text = r"$e$"
    expected_tokens = [
        Token(TokenType.MATH_SHIFT_INLINE, "$", 0),
        Token(TokenType.CHARACTER, "e", 1, Catcode.LETTER),
        Token(TokenType.MATH_SHIFT_INLINE, "$", 2),
    ]
    assert_tokenizer_sequence(tokenizer, text, expected_tokens)

    # change catcode of $ to LETTER
    tokenizer.set_catcode(ord("$"), Catcode.LETTER)
    expected_tokens2 = [
        Token(TokenType.CHARACTER, "$", 0, Catcode.LETTER),
        Token(TokenType.CHARACTER, "e", 1, Catcode.LETTER),
        Token(TokenType.CHARACTER, "$", 2, Catcode.LETTER),
    ]
    assert_tokenizer_sequence(tokenizer, text, expected_tokens2)

    # test display math
    text = r"$$e$$"
    expected_tokens3 = [
        Token(TokenType.MATH_SHIFT_DISPLAY, "$$", 0),
        Token(TokenType.CHARACTER, "e", 2, Catcode.LETTER),
        Token(TokenType.MATH_SHIFT_DISPLAY, "$$", 3),
    ]
