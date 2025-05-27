from typing import List
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import (
    WHITESPACE_TOKEN,
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


def is_mathshift_token(tok: Token) -> bool:
    return (
        tok.type == TokenType.MATH_SHIFT_INLINE
        or tok.type == TokenType.MATH_SHIFT_DISPLAY
    )


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


def is_signed_integer_token(tok: Token) -> bool:
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


def strip_whitespace_tokens(tokens: List[Token]) -> List[Token]:
    # strip whitespace tokens from the beginning and end of the list
    while tokens and is_whitespace_token(tokens[0]):
        tokens.pop(0)
    while tokens and is_whitespace_token(tokens[-1]):
        tokens.pop()
    return tokens


def substitute_token_args(
    definition: List[Token],
    args: List[List[Token]],
    math_mode: bool = False,
) -> List[Token]:

    out: List[Token] = []

    for token in definition:
        if token.type == TokenType.PARAMETER:
            index = int(token.value) - 1
            if index < len(args):
                if math_mode:
                    math_out = [
                        WHITESPACE_TOKEN.copy(),
                        *args[index],
                        WHITESPACE_TOKEN.copy(),
                    ]
                    out.extend(math_out)
                else:
                    out.extend(args[index])

        else:
            out.append(token)

    # if math_mode:
    #     out = [
    #         WHITESPACE_TOKEN.copy(),
    #         *out,
    #         WHITESPACE_TOKEN.copy(),
    #     ]

    return out
