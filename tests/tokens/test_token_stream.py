import pytest
from typing import List

from latex2json.tokens import Tokenizer, TokenType, Catcode, Token, TokenStream


def assert_stream_sequence(
    stream: TokenStream, expected_tokens: List[Token], skip_whitespace: bool = True
):
    i = 0
    while not stream.eof():
        if skip_whitespace:
            tok = stream.skip_whitespace()
        tok = stream.consume()
        assert tok == expected_tokens[i]
        i += 1

    assert i == len(expected_tokens)


def test_token_stream():
    text = r"""
    \Hello, % world!
    BRO
    \\
    """.strip()
    tokenizer = Tokenizer()
    stream = TokenStream(tokenizer=tokenizer)
    stream.set_text(text)

    bro_start = text.find("BRO")
    expected_tokens = [
        Token(TokenType.CONTROL_SEQUENCE, "Hello", 0),
        Token(TokenType.CHARACTER, ",", 6, Catcode.OTHER),
        # Token(TokenType.END_OF_LINE, "\n", text.find("\n")),
        Token(TokenType.CHARACTER, "B", bro_start, Catcode.LETTER),
        Token(TokenType.CHARACTER, "R", bro_start + 1, Catcode.LETTER),
        Token(TokenType.CHARACTER, "O", bro_start + 2, Catcode.LETTER),
        # Token(TokenType.END_OF_LINE, "\n", text.find("\n", bro_start + 3)),
        Token(TokenType.CONTROL_SEQUENCE, "\\", text.find(r"\\")),
    ]

    assert_stream_sequence(stream, expected_tokens, skip_whitespace=True)

    assert stream.eof()

    # # test go_previous
    # stream.go_previous()
    # assert stream.consume() == expected_tokens[-1]

    stream.reset()
    assert stream.pos == 0 and not stream.eof()

    assert stream.peek() == expected_tokens[0]
    stream.consume()
    assert stream.peek() == expected_tokens[1]


def test_skip_ignored():
    tokenizer = Tokenizer()

    # make ~ ignored
    tokenizer.set_catcode(ord("~"), Catcode.IGNORED)

    text = r"~ Hi there ~ [}"
    stream = TokenStream(tokenizer=tokenizer)
    stream.set_text(text)

    expected_tokens = [
        Token(TokenType.CHARACTER, " ", 1, Catcode.SPACE),
        Token(TokenType.CHARACTER, "H", 2, Catcode.LETTER),
        Token(TokenType.CHARACTER, "i", 3, Catcode.LETTER),
        Token(TokenType.CHARACTER, " ", 4, Catcode.SPACE),
        Token(TokenType.CHARACTER, "t", 5, Catcode.LETTER),
        Token(TokenType.CHARACTER, "h", 6, Catcode.LETTER),
        Token(TokenType.CHARACTER, "e", 7, Catcode.LETTER),
        Token(TokenType.CHARACTER, "r", 8, Catcode.LETTER),
        Token(TokenType.CHARACTER, "e", 9, Catcode.LETTER),
        Token(TokenType.CHARACTER, " ", 10, Catcode.SPACE),
        Token(TokenType.CHARACTER, " ", 12, Catcode.SPACE),
        Token(TokenType.CHARACTER, "[", 13, Catcode.OTHER),
        Token(TokenType.CHARACTER, "}", 14, Catcode.END_GROUP),
    ]
    assert_stream_sequence(stream, expected_tokens, skip_whitespace=False)

    # reset and test peek
    stream.reset()
    assert stream.peek() == expected_tokens[0]
    assert stream.peek(3) == expected_tokens[3]
