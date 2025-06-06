from typing import List
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import split_tokens_by_predicate


def is_comma_token(tok: Token) -> bool:
    return tok.value == "," and tok.catcode == Catcode.OTHER


def is_slash_token(tok: Token) -> bool:
    return tok.value == "/" and tok.catcode == Catcode.OTHER


def replace_for_each_item_body(
    body_tokens: List[Token], variables: List[Token], split_args: List[List[Token]]
):
    out_tokens: List[Token] = []
    total_split_args = len(split_args)
    if total_split_args == 0:
        return []

    # Create a mapping of variable names to their replacement values
    var_map = {}
    for i, var in enumerate(variables):
        var_map[var.value] = split_args[i % total_split_args]

    # Process each token in the body
    for token in body_tokens:
        # If token is a control sequence and it's one of our variables
        if token.type == TokenType.CONTROL_SEQUENCE and token.value in var_map:
            # Add the replacement tokens
            out_tokens.extend(var_map[token.value])
        else:
            # Keep the original token
            out_tokens.append(token.copy())

    return out_tokens


def for_each_handler(expander: ExpanderCore, token: Token):
    r"""
    \foreach \var1/\var2 in {val1/val2, val3/val4} { body }
    \foreach \var in {list} { body }

    Usage: 
    \foreach \i/\j in {1/2,2/3,3/4,4/5,5/6} {
        This is item number \i \j. \\
    }
    """
    expander.skip_whitespace()
    variables: List[Token] = []

    tok = expander.peek()
    while tok:
        if tok.type == TokenType.CONTROL_SEQUENCE:
            variables.append(tok)
        elif tok.value == "/" or tok.value == " ":
            pass
        else:
            break
        expander.consume()
        tok = expander.peek()

    if not expander.parse_keyword("in "):
        expander.logger.warning(r"\foreach expected 'in' after variables")
        return None

    expander.skip_whitespace()
    list_tokens = expander.parse_brace_as_tokens()
    if not list_tokens:
        expander.logger.warning(r"\foreach expected list after 'in'")
        return None

    expander.skip_whitespace()
    body_tokens = expander.parse_brace_as_tokens()
    if not body_tokens:
        expander.logger.warning(r"\foreach expected body after list")
        return None

    # split list tokens into groups by ','
    list_items = split_tokens_by_predicate(list_tokens, is_comma_token)

    N_vars = len(variables)

    result_tokens: List[Token] = []
    for item in list_items:
        # Split the current item by '/' to get individual values
        split = (
            split_tokens_by_predicate(item, is_slash_token)[:N_vars]
            if N_vars > 1
            else [item]
        )

        out_tokens = replace_for_each_item_body(body_tokens, variables, split)
        result_tokens.extend(out_tokens)

    expander.push_tokens(result_tokens)
    return []


def register_for_each_handlers(expander: ExpanderCore):
    expander.register_handler("foreach", for_each_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    text = r"""
    \begin{itemize}
    \foreach \fruit in {apple, banana, orange} {
        \item I like \fruit
    }
    \end{itemize}
""".strip()

    expander = Expander()
    register_for_each_handlers(expander)
    out = expander.expand(text)
    # print(expander.get_tokens())
