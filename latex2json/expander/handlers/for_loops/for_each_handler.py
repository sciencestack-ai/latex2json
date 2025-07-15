from typing import List
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import (
    split_tokens_by_predicate,
    strip_whitespace_tokens,
    is_comma_token,
)


def is_slash_token(tok: Token) -> bool:
    return tok.value == "/" and tok.catcode == Catcode.OTHER


def make_handler(tokens: List[Token]):
    return lambda expander, token: tokens.copy()


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
    if list_tokens is None:
        expander.logger.warning(r"\foreach expected list after 'in'")
        return None

    expander.skip_whitespace()
    body_tokens = expander.parse_brace_as_tokens()
    if body_tokens is None:
        expander.logger.warning(r"\foreach expected body after list")
        return None
    elif len(body_tokens) == 0:
        return []

    # split list tokens into groups by ','
    list_items = split_tokens_by_predicate(list_tokens, is_comma_token)
    # for the case of trailing ',', basically means next is empty item
    if list_tokens and is_comma_token(list_tokens[-1]):
        list_items.append([])

    N_vars = len(variables)

    expander.push_scope()  # push a new scope to define the local macros

    result_tokens: List[Token] = []

    for item in list_items:
        # Split the current item by '/' to get individual values
        # \foreach \var1/\var2 in {val1/val2, val3/val4} -> [val1, val2], [val3, val4]
        split = (
            split_tokens_by_predicate(item, is_slash_token)[:N_vars]
            if N_vars > 1
            else [item]
        )

        # in latex, we lstrip whitespace after the comma e.g. ' val3/val4' -> 'val3/val4'
        split_args = [
            strip_whitespace_tokens(arg, lstrip=True, rstrip=False) for arg in split
        ]
        total_split_args = len(split_args)
        if total_split_args > 0:
            # \define \var1, \var2, etc. as local macros that hold the item tokens
            for i, var in enumerate(variables):

                var_name = var.to_str()
                item_tokens = split_args[i % total_split_args]

                # define the variable name as a local macro that holds the item tokens
                expander.register_handler(
                    var_name, make_handler(item_tokens), is_global=False
                )
        # then exec/expand the body tokens
        result_tokens.extend(expander.expand_tokens(body_tokens))

    expander.pop_scope()

    return result_tokens


def register_for_each_handlers(expander: ExpanderCore):
    expander.register_handler("foreach", for_each_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    text = r"\foreach \x/\y/\z in {a/b, c/d} {\x-\y-\z }"

    expander = Expander()
    register_for_each_handlers(expander)
    out = expander.expand(text)
    # print(expander.get_tokens())
