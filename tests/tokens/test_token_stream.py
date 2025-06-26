import pytest
from typing import List

from latex2json.tokens import Tokenizer, TokenType, Catcode, Token
from latex2json.tokens.token_stream import (
    TokenStream,
)


def assert_stream_sequence(
    stream: TokenStream, expected_tokens: List[Token], skip_whitespace: bool = True
):
    i = 0
    while not stream.eof():
        if skip_whitespace:
            stream.skip_whitespace()
        tok = stream.consume()
        assert tok == expected_tokens[i]
        i += 1

    assert i == len(expected_tokens)


def test_push_text():
    stream = TokenStream()
    stream.push_text("12345")

    assert stream.consume() == Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER)
    assert stream.consume() == Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER)

    # now insert new text
    stream.push_text("abcdefg")
    assert stream.consume() == Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER)
    assert stream.consume() == Token(TokenType.CHARACTER, "b", catcode=Catcode.LETTER)
    assert stream.consume() == Token(TokenType.CHARACTER, "c", catcode=Catcode.LETTER)
    assert stream.consume() == Token(TokenType.CHARACTER, "d", catcode=Catcode.LETTER)
    assert stream.consume() == Token(TokenType.CHARACTER, "e", catcode=Catcode.LETTER)
    assert stream.consume() == Token(TokenType.CHARACTER, "f", catcode=Catcode.LETTER)
    assert stream.consume() == Token(TokenType.CHARACTER, "g", catcode=Catcode.LETTER)

    # now resume back to the original text
    assert stream.consume() == Token(TokenType.CHARACTER, "3", catcode=Catcode.OTHER)
    assert stream.consume() == Token(TokenType.CHARACTER, "4", catcode=Catcode.OTHER)
    assert stream.consume() == Token(TokenType.CHARACTER, "5", catcode=Catcode.OTHER)

    assert stream.eof()


def test_push_tokens():
    stream = TokenStream()
    stream.push_tokens(
        [
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "3", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "4", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "5", catcode=Catcode.OTHER),
        ]
    )
    assert stream.consume() == Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER)
    assert stream.consume() == Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER)

    # now test with push_text
    stream.push_text("abc")
    assert stream.consume() == Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER)
    assert stream.consume() == Token(TokenType.CHARACTER, "b", catcode=Catcode.LETTER)

    # now test with push_tokens again
    stream.push_tokens(
        [
            Token(TokenType.CHARACTER, "6", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "7", catcode=Catcode.OTHER),
        ]
    )
    assert stream.consume() == Token(TokenType.CHARACTER, "6", catcode=Catcode.OTHER)
    assert stream.consume() == Token(TokenType.CHARACTER, "7", catcode=Catcode.OTHER)

    # now its back at abc -> c
    assert stream.consume() == Token(TokenType.CHARACTER, "c", catcode=Catcode.LETTER)

    # now its back at "12345" -> 345
    assert stream.consume() == Token(TokenType.CHARACTER, "3", catcode=Catcode.OTHER)
    assert stream.consume() == Token(TokenType.CHARACTER, "4", catcode=Catcode.OTHER)

    assert not stream.eof()

    # check set_text resets all
    stream.set_text("123")
    assert stream.consume() == Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER)
    assert stream.consume() == Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER)
    assert stream.consume() == Token(TokenType.CHARACTER, "3", catcode=Catcode.OTHER)

    assert stream.eof()


def test_token_stream():
    text = r"""
    \Hello, % world!
    BRO
    \\
    """.strip()

    stream = TokenStream(Tokenizer())
    stream.push_text(text)

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


def test_token_stream_match():
    stream = TokenStream()
    stream.push_tokens(
        [
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.END_OF_LINE, "\n"),
            Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
        ]
    )
    assert stream.match(TokenType.CHARACTER, "1")
    assert stream.consume() == Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER)
    assert stream.peek() == Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE)
    assert stream.match(TokenType.CHARACTER, "2")


def test_skip_ignored():
    tokenizer = Tokenizer()

    # make ~ ignored
    tokenizer.set_catcode(ord("~"), Catcode.IGNORED)

    text = r"~ Hi there ~ [}"
    stream = TokenStream(tokenizer=tokenizer)
    stream.push_text(text)

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
