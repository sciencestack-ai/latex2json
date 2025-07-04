from typing import Callable, List
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import (
    BEGIN_BRACE_TOKEN,
    END_BRACE_TOKEN,
    WHITESPACE_TOKEN,
    EnvironmentStartToken,
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


def is_begin_parenthesis_token(tok: Token) -> bool:
    return (
        tok.type == TokenType.CHARACTER
        and tok.catcode == Catcode.OTHER
        and tok.value == "("
    )


def is_end_parenthesis_token(tok: Token) -> bool:
    return (
        tok.type == TokenType.CHARACTER
        and tok.catcode == Catcode.OTHER
        and tok.value == ")"
    )


def is_whitespace_token(tok: Token) -> bool:
    if tok.type == TokenType.END_OF_LINE:
        return True
    return tok.type == TokenType.CHARACTER and tok.catcode == Catcode.SPACE


def is_asterisk_token(tok: Token) -> bool:
    return (
        # tok.type == TokenType.CHARACTER and
        tok.catcode == Catcode.OTHER
        and tok.value == "*"
    )


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


def strip_whitespace_tokens(
    tokens: List[Token], lstrip=True, rstrip=True
) -> List[Token]:
    # strip whitespace tokens from the beginning and end of the list
    if lstrip:
        while tokens and is_whitespace_token(tokens[0]):
            tokens.pop(0)
    if rstrip:
        while tokens and is_whitespace_token(tokens[-1]):
            tokens.pop()
    return tokens


def wrap_tokens_in_braces(tokens: List[Token]) -> List[Token]:
    if not tokens:
        return tokens
    if tokens[0] == BEGIN_BRACE_TOKEN and tokens[-1] == END_BRACE_TOKEN:
        return tokens
    return [
        BEGIN_BRACE_TOKEN.copy(),
        *tokens,
        END_BRACE_TOKEN.copy(),
    ]


def is_alignment_token(tok: Token) -> bool:
    return (
        # tok.type == TokenType.CHARACTER and
        tok.catcode == Catcode.ALIGNMENT_TAB
        or (tok.value == "&" and tok.catcode == Catcode.ACTIVE)  # mathmode
    )


def is_newline_token(tok: Token) -> bool:
    # Not to be confused with \n
    return tok.type == TokenType.CONTROL_SEQUENCE and tok.value == "\\"


def substitute_token_args(
    definition: List[Token],
    args: List[List[Token]],
    math_mode: bool = False,
) -> List[Token]:

    out: List[Token] = []

    for i, token in enumerate(definition):
        if token.type == TokenType.PARAMETER:
            # replace parameter with argument
            index = int(token.value) - 1
            if index < len(args):
                arg = args[index]
                if math_mode:
                    # check if prev/next token is { and }. If so, we dont need to wrap in braces
                    is_prev_brace = i > 0 and definition[i - 1] == BEGIN_BRACE_TOKEN
                    is_next_brace = (
                        i < len(definition) - 1 and definition[i + 1] == END_BRACE_TOKEN
                    )
                    if not (is_prev_brace and is_next_brace):
                        arg = wrap_tokens_in_braces(arg)
                out.extend(arg)
        else:
            out.append(token)

    if math_mode and out:
        # check if first or last token is a trailing character. If so, wrap in braces
        if out[0].type == TokenType.CHARACTER or out[-1].type == TokenType.CHARACTER:
            if not (out[0] == BEGIN_BRACE_TOKEN and out[-1] == END_BRACE_TOKEN):
                out = wrap_tokens_in_braces(out)

    return out


def split_tokens_by_predicate(
    tokens: List[Token], is_separator: Callable[[Token], bool]
) -> List[List[Token]]:
    """Generic function to split tokens into groups based on a separator predicate.

    Args:
        tokens: List of tokens to split
        is_separator: Function that returns True for tokens that mark group boundaries

    Returns:
        List of token groups
    """
    groups: List[List[Token]] = []
    current_group: List[Token] = []

    for tok in tokens:
        if is_separator(tok):
            groups.append(current_group)
            current_group = []
        else:
            current_group.append(tok)

    if current_group:
        groups.append(current_group)

    return groups


def segment_tokens_by_begin_end(tokens: List[Token]) -> List[List[Token]]:
    """Segment tokens into groups based on begin and end tokens.

    Args:
        tokens: List of tokens to segment

    Returns:
        List of token groups
    """
    groups: List[List[Token]] = []
    current_group: List[Token] = []
    env_name: str | None = None

    for tok in tokens:
        if isinstance(tok, EnvironmentStartToken):
            groups.append(current_group)
            current_group = [tok]  # Start new group with begin token
            env_name = tok.name
        elif tok.type == TokenType.ENVIRONMENT_END:
            if tok.value == env_name:  # Found matching end token
                current_group.append(tok)
                groups.append(current_group)
                current_group = []
                env_name = None
            else:
                current_group.append(tok)
        else:
            current_group.append(tok)

    if current_group:
        groups.append(current_group)

    return groups
