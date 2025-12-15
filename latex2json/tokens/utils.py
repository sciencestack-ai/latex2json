from dataclasses import dataclass
from typing import Callable, List, Optional
from latex2json.tokens.catcodes import DEFAULT_CATCODES, Catcode
from latex2json.tokens.types import (
    BEGIN_BRACE_TOKEN,
    BEGIN_BRACKET_TOKEN,
    END_BRACE_TOKEN,
    END_BRACKET_TOKEN,
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


def is_comma_token(tok: Token) -> bool:
    return tok.value == "," and tok.catcode == Catcode.OTHER


def is_equals_token(tok: Token) -> bool:
    return tok.value == "=" and tok.catcode == Catcode.OTHER


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
    if tokens and tokens[0] == BEGIN_BRACE_TOKEN and tokens[-1] == END_BRACE_TOKEN:
        return tokens
    return [
        BEGIN_BRACE_TOKEN.copy(),
        *tokens,
        END_BRACE_TOKEN.copy(),
    ]


def wrap_tokens_in_brackets(tokens: List[Token]) -> List[Token]:
    if tokens and tokens[0] == BEGIN_BRACKET_TOKEN and tokens[-1] == END_BRACKET_TOKEN:
        return tokens
    return [
        BEGIN_BRACKET_TOKEN.copy(),
        *tokens,
        END_BRACKET_TOKEN.copy(),
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
) -> List[Token]:

    out: List[Token] = []

    for i, token in enumerate(definition):
        if token.type == TokenType.PARAMETER:
            # replace parameter with argument
            index = int(token.value) - 1
            if index < len(args):
                arg = args[index]
                out.extend(arg)
        else:
            out.append(token)

    return out


def find_token_sequence(haystack: List[Token], needle: List[Token]) -> int:
    """
    Find the first occurrence of needle token sequence in haystack token sequence.

    Args:
        haystack: The token list to search in
        needle: The token sequence to search for

    Returns:
        The index of the first occurrence of needle in haystack, or -1 if not found
    """
    if not needle:
        return 0
    if not haystack or len(needle) > len(haystack):
        return -1

    needle_len = len(needle)
    for i in range(len(haystack) - needle_len + 1):
        # Check if all tokens match starting at position i
        if all(haystack[i + j] == needle[j] for j in range(needle_len)):
            return i

    return -1


def split_tokens_by_predicate(
    tokens: List[Token],
    is_separator: Callable[[Token], bool],
    brace_check=True,
    incl_braces=False,
    incl_separator=False,
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
    brace_depth = 0

    for tok in tokens:
        if brace_check and tok.type == TokenType.CHARACTER:
            if tok.value == "{":
                brace_depth += 1
                if incl_braces:
                    current_group.append(tok)
                continue
            elif tok.value == "}":
                brace_depth = max(0, brace_depth - 1)  # Prevent negative depth
                if incl_braces:
                    current_group.append(tok)
                continue

        if brace_depth == 0 and is_separator(tok):
            groups.append(current_group)
            current_group = []
            if incl_separator:
                current_group.append(tok)
        else:
            current_group.append(tok)

    if current_group:
        groups.append(current_group)

    return groups


def segment_tokens_by_begin_end(tokens: List[Token]) -> List[List[Token]]:
    """Segment tokens into groups based on begin and end tokens.

    Properly handles nested environments by using a stack to track environment names.

    Args:
        tokens: List of tokens to segment

    Returns:
        List of token groups
    """
    groups: List[List[Token]] = []
    current_group: List[Token] = []
    env_stack: List[str] = []  # Stack to track nested environment names

    for tok in tokens:
        if isinstance(tok, EnvironmentStartToken):
            if not env_stack:
                # Starting a new top-level environment
                groups.append(current_group)
                current_group = [tok]
            else:
                # Nested environment - add to current group
                current_group.append(tok)
            env_stack.append(tok.name)
        elif tok.type == TokenType.ENVIRONMENT_END:
            current_group.append(tok)
            # Check if this end matches the most recent begin
            if env_stack and tok.value == env_stack[-1]:
                env_stack.pop()
                # If stack is empty, we've closed the top-level environment
                if not env_stack:
                    groups.append(current_group)
                    current_group = []
        else:
            current_group.append(tok)

    if current_group:
        groups.append(current_group)

    return groups


@dataclass
class Segment:
    tokens: List[Token]
    is_group: bool


def segment_tokens_by_begin_end_and_braces(tokens: List[Token]) -> List[Segment]:
    """Segment tokens into groups based on begin and end tokens, and braces."""

    # first, split into begin_end
    groups: List[Segment] = []
    current_group: List[Token] = []
    brace_depth = 0

    def push_to_stack():
        nonlocal current_group
        if current_group:
            first_tok = current_group[0]
            is_group = (
                is_begin_group_token(first_tok)
                or first_tok.type == TokenType.ENVIRONMENT_START
            )
            groups.append(Segment(current_group, is_group=is_group))
        current_group = []

    # first split begin end
    begin_end_groups = segment_tokens_by_begin_end(tokens)
    for segment in begin_end_groups:
        if not segment:
            continue
        first_tok = segment[0]
        # if begin segment
        if first_tok.type == TokenType.ENVIRONMENT_START:
            if brace_depth == 0:
                push_to_stack()  # push existing buffer to stack
                current_group.extend(segment)
                push_to_stack()  # push begin/end segment to stack
            else:
                current_group.extend(segment)
            continue

        # non begin/end segments
        for token in segment:
            # check for braces
            if is_begin_group_token(token):
                if brace_depth == 0:
                    push_to_stack()
                brace_depth += 1
            elif is_end_group_token(token):
                brace_depth -= 1
                if brace_depth == 0:
                    current_group.append(token)
                    push_to_stack()
                    continue
            current_group.append(token)

    push_to_stack()

    return groups


def convert_str_to_tokens(text: str, catcode: Optional[Catcode] = None) -> List[Token]:
    out = []
    for t in text:
        c = catcode or DEFAULT_CATCODES[ord(t)]
        out.append(Token(TokenType.CHARACTER, t, catcode=c))
    return out


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    text = r"""
    \begin{xxx}
    \end{xxx} 
    sometext
    {aaa \\ bbb} 
    ccc
    {
    BRACE
    \begin{yyy}
    \end{yyy}
    }
    """.strip()
    tokens = expander.expand(text)
    groups = segment_tokens_by_begin_end_and_braces(tokens)
    for i, group in enumerate(groups):
        print(f"GROUP {i}: {group.is_group}")
        tok_str = expander.convert_tokens_to_str(group.tokens).strip()
        print(tok_str)
