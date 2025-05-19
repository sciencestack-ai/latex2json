from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import (
    Token,
    TokenType,
)


def is_text_token(tok: Token) -> bool:
    # a-z, A-Z, 0-9, punctuation etc.
    # These are regular characters that form text.
    return tok.type == TokenType.CHARACTER and tok.catcode in [
        Catcode.LETTER,
        Catcode.OTHER,
    ]


def is_begin_group_token(tok: Token) -> bool:
    return tok.type == TokenType.CHARACTER and tok.catcode == Catcode.BEGIN_GROUP


def is_end_group_token(tok: Token) -> bool:
    return tok.type == TokenType.CHARACTER and tok.catcode == Catcode.END_GROUP


def is_begin_bracket_token(tok: Token) -> bool:
    return (
        tok.type == TokenType.CHARACTER
        and tok.catcode == Catcode.OTHER
        and tok.value == "["
    )


def is_end_bracket_token(tok: Token) -> bool:
    return (
        tok.type == TokenType.CHARACTER
        and tok.catcode == Catcode.OTHER
        and tok.value == "]"
    )


def is_whitespace_token(tok: Token) -> bool:
    if tok.type == TokenType.END_OF_LINE:
        return True
    return tok.type == TokenType.CHARACTER and tok.catcode == Catcode.SPACE


def is_integer_token(tok: Token) -> bool:
    return is_digit_token(tok) and tok.value != "."


def is_1_to_9_token(tok: Token) -> bool:
    return (
        tok.type == TokenType.CHARACTER
        and tok.catcode == Catcode.OTHER
        and "1" <= tok.value <= "9"
    )


def is_digit_token(tok: Token) -> bool:
    return (
        tok.type == TokenType.CHARACTER
        and tok.catcode == Catcode.OTHER
        and (tok.value.isdigit() or tok.value in ["-", "+", "."])
    )


def is_param_token(tok: Token) -> bool:
    return tok.type == TokenType.CHARACTER and tok.catcode == Catcode.PARAMETER
