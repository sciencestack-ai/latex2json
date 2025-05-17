import pytest
from typing import List

from latex2json.tokens import Tokenizer, TokenType, Catcode, Token
from latex2json.tokens.token_stream import (
    BaseTokenStream,
    TokenStream,
    MultiTokenStream,
)


def assert_stream_sequence(
    stream: BaseTokenStream, expected_tokens: List[Token], skip_whitespace: bool = True
):
    i = 0
    while not stream.eof():
        if skip_whitespace:
            stream.skip_whitespace()
        tok = stream.consume()
        assert tok == expected_tokens[i]
        i += 1

    assert i == len(expected_tokens)


def test_token_stream(stream: BaseTokenStream = BaseTokenStream(tokenizer=Tokenizer())):
    text = r"""
    \Hello, % world!
    BRO
    \\
    """.strip()
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
    assert stream.get_pos()[0] == 0 and not stream.eof()

    assert stream.peek() == expected_tokens[0]
    stream.consume()
    assert stream.peek() == expected_tokens[1]


def test_skip_ignored():
    tokenizer = Tokenizer()

    # make ~ ignored
    tokenizer.set_catcode(ord("~"), Catcode.IGNORED)

    text = r"~ Hi there ~ [}"
    stream = BaseTokenStream(tokenizer=tokenizer)
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


def test_token_stream_with_buffer():
    tokenizer = Tokenizer()
    stream = TokenStream(tokenizer=tokenizer)

    test_token_stream(stream)

    text = r"123   456"
    stream.set_text(text)
    assert stream.peek() == Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER)
    stream.consume()
    assert stream.peek() == Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER)

    # test push_tokens
    stream.push_tokens(
        [
            Token(TokenType.CHARACTER, "7", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "8", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "9", catcode=Catcode.OTHER),
        ]
    )
    assert stream.peek() == Token(TokenType.CHARACTER, "7", catcode=Catcode.OTHER)
    stream.consume()
    # test pop_tokens
    stream.pop_tokens()
    assert stream.peek() == Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER)
    stream.consume()
    assert stream.peek() == Token(TokenType.CHARACTER, "3", catcode=Catcode.OTHER)
    stream.consume()
    cur_base_pos = stream.get_pos()

    # check that skip_whitespace skips past the buffer too
    stream.push_tokens(
        [
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        ]
    )
    stream.get_pos() == (0, 1)
    preskip_pos = stream.skip_whitespace()
    # test that preskip_pos now uses base stream since skip_whitespace has gone past the buffer
    assert preskip_pos == cur_base_pos

    assert stream.peek() == Token(TokenType.CHARACTER, "4", catcode=Catcode.OTHER)
    cur_pos = (text.find("4"), 0)
    assert stream.get_pos() == cur_pos

    # test that set_pos after buffer is gone does not work
    stream.set_pos(1, 1)
    assert stream.get_pos() == cur_pos

    # test set_pos
    stream.set_pos(text.find("6"), 0)
    assert stream.peek() == Token(TokenType.CHARACTER, "6", catcode=Catcode.OTHER)

    # test get_pos/set_pos with stacks
    stream.push_tokens(
        [
            Token(TokenType.CHARACTER, "7", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "8", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "9", catcode=Catcode.OTHER),
        ]
    )
    assert stream.get_pos() == (0, 1)
    assert stream.consume() == Token(TokenType.CHARACTER, "7", catcode=Catcode.OTHER)
    assert stream.get_pos() == (1, 1)
    stream.set_pos(0, 1)
    assert stream.consume() == Token(TokenType.CHARACTER, "7", catcode=Catcode.OTHER)

    stream.pop_tokens()

    # back to base stream pos
    assert stream.get_pos() == (text.find("6"), 0)


def test_multi_tokenizer_stream():
    tokenizer = Tokenizer()
    stream = BaseTokenStream(tokenizer=tokenizer)
    stream.set_text(r"123")
    multi_stream = MultiTokenStream([stream])
    assert multi_stream.peek() == Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER)
    multi_stream.consume()

    # now add tokens
    multi_stream.push_tokens(
        [
            Token(TokenType.CHARACTER, "H", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "e", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "l", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "l", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "o", catcode=Catcode.LETTER),
        ]
    )
    assert multi_stream.peek() == Token(
        TokenType.CHARACTER, "H", catcode=Catcode.LETTER
    )
    multi_stream.consume()
    assert multi_stream.peek() == Token(
        TokenType.CHARACTER, "e", catcode=Catcode.LETTER
    )

    # now pop it
    multi_stream.pop_tokens()
    # back to the original stream
    assert multi_stream.peek() == Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER)
    multi_stream.consume()
    assert multi_stream.peek() == Token(TokenType.CHARACTER, "3", catcode=Catcode.OTHER)
    multi_stream.consume()
    assert multi_stream.eof()

    # add back some tokens
    multi_stream.push_tokens(
        [
            Token(TokenType.CONTROL_SEQUENCE, "foo"),
        ]
    )
    # add 2nd layer of tokens
    multi_stream.push_tokens(
        [
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "3", catcode=Catcode.OTHER),
        ]
    )
    assert not multi_stream.eof()

    # consume top layer
    assert multi_stream.consume() == Token(
        TokenType.CHARACTER, "1", catcode=Catcode.OTHER
    )
    assert multi_stream.consume() == Token(
        TokenType.CHARACTER, "2", catcode=Catcode.OTHER
    )
    assert multi_stream.consume() == Token(
        TokenType.CHARACTER, "3", catcode=Catcode.OTHER
    )
    # consume next layer
    assert multi_stream.consume() == Token(TokenType.CONTROL_SEQUENCE, "foo")
    # finish
    assert multi_stream.eof()

    # now finally, test the multi-tokenizer stream
    test_token_stream(multi_stream)


def test_multi_tokenizer_stream():
    stream = BaseTokenStream(tokenizer=Tokenizer())
    stream.set_text(r"123")
    stream2 = BaseTokenStream(tokenizer=Tokenizer())
    stream2.set_text(r"456")
    multi_stream = MultiTokenStream([stream, stream2])
    assert multi_stream.consume() == Token(
        TokenType.CHARACTER, "4", catcode=Catcode.OTHER
    )
    assert multi_stream.consume() == Token(
        TokenType.CHARACTER, "5", catcode=Catcode.OTHER
    )
    assert multi_stream.consume() == Token(
        TokenType.CHARACTER, "6", catcode=Catcode.OTHER
    )
    assert multi_stream.consume() == Token(
        TokenType.CHARACTER, "1", catcode=Catcode.OTHER
    )
    assert multi_stream.consume() == Token(
        TokenType.CHARACTER, "2", catcode=Catcode.OTHER
    )
    assert multi_stream.consume() == Token(
        TokenType.CHARACTER, "3", catcode=Catcode.OTHER
    )
    assert multi_stream.eof()


def test_multi_stream_skip_whitespace():
    tokenizer = Tokenizer()
    stream = BaseTokenStream(tokenizer=tokenizer)
    stream.set_text(r"1  2  3")
    multi_stream = MultiTokenStream([stream])

    assert multi_stream.consume() == Token(
        TokenType.CHARACTER, "1", catcode=Catcode.OTHER
    )

    multi_stream.push_tokens(
        [
            Token(TokenType.CHARACTER, "H", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        ]
    )
    assert multi_stream.consume() == Token(
        TokenType.CHARACTER, "H", catcode=Catcode.LETTER
    )
    assert multi_stream.consume() == Token(
        TokenType.CHARACTER, " ", catcode=Catcode.SPACE
    )
    # notice the whitespace skips past the stack to the next stack as well
    multi_stream.skip_whitespace()
    # already at base stack
    assert multi_stream.consume() == Token(
        TokenType.CHARACTER, "2", catcode=Catcode.OTHER
    )
    multi_stream.skip_whitespace()
    assert multi_stream.consume() == Token(
        TokenType.CHARACTER, "3", catcode=Catcode.OTHER
    )
    assert multi_stream.eof()
