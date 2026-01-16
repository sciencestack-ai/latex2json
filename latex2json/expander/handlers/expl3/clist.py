"""
expl3 comma list (clist) handlers.

Handles \clist_new:N, \clist_clear:N, \clist_set:Nn, \clist_map_inline:Nn,
\clist_put_right:Nn, and related functions.

Storage format: comma lists store items comma-separated: item1,item2,item3
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
def _make_brace_tokens(tokens: List[Token]) -> List[Token]:
    """Wrap tokens in braces (always, unlike _make_brace_tokens)."""
    return [
        Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
        *tokens,
        Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
    ]


def clist_new_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \clist_new:N \l_my_clist  ->  \def\l_my_clist{}
    """
    expander.skip_whitespace()
    var = expander.consume()
    if var:
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
                Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
                Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
            ]
        )
    return []


def clist_clear_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_clear:N \l_my_clist  ->  \def\l_my_clist{}
    """
    return clist_new_handler(expander, _token)


def clist_set_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_set:Nn \l_my_clist {a,b,c}  ->  \def\l_my_clist{a,b,c}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    value = expander.parse_brace_as_tokens() or []

    if var:
        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
            + _make_brace_tokens(value)
        )
    return []


def clist_gset_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_gset:Nn \g_my_clist {a,b,c}  ->  \global\def\g_my_clist{a,b,c}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    value = expander.parse_brace_as_tokens() or []

    if var:
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "global"),
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
            ]
            + _make_brace_tokens(value)
        )
    return []


def _parse_clist_items(tokens: List[Token]) -> List[List[Token]]:
    """
    Parse comma-separated tokens into individual items.
    Handles nested braces correctly.
    """
    items = []
    current_item = []
    depth = 0

    for tok in tokens:
        if tok.catcode == Catcode.BEGIN_GROUP or (
            tok.type == TokenType.CHARACTER and tok.value == "{"
        ):
            depth += 1
            current_item.append(tok)
        elif tok.catcode == Catcode.END_GROUP or (
            tok.type == TokenType.CHARACTER and tok.value == "}"
        ):
            depth -= 1
            current_item.append(tok)
        elif tok.value == "," and depth == 0:
            # End of current item
            stripped = _strip_whitespace_tokens(current_item)
            if stripped:  # Only add non-empty items
                items.append(stripped)
            current_item = []
        else:
            current_item.append(tok)

    # Don't forget the last item
    stripped = _strip_whitespace_tokens(current_item)
    if stripped:  # Only add non-empty items
        items.append(stripped)

    return items


def _strip_whitespace_tokens(tokens: List[Token]) -> List[Token]:
    """Strip leading and trailing whitespace tokens."""
    # Strip leading
    start = 0
    while start < len(tokens) and tokens[start].value.isspace():
        start += 1
    # Strip trailing
    end = len(tokens)
    while end > start and tokens[end - 1].value.isspace():
        end -= 1
    return tokens[start:end]


def clist_map_inline_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_map_inline:Nn \l_my_clist {code with #1}
    Iterates over clist items, replacing #1 with each item.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    body = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        clist_tokens = macro.definition if macro and macro.definition else []
        items = _parse_clist_items(clist_tokens)

        # Build result: for each item, substitute #1 in body
        result_tokens = []
        for item in items:
            for tok in body:
                if tok.type == TokenType.PARAMETER and tok.value == "1":
                    result_tokens.extend(item)
                else:
                    result_tokens.append(tok)

        expander.push_tokens(result_tokens)
    return []


def clist_map_inline_n_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_map_inline:nn {a,b,c} {code with #1}
    Iterates over inline clist, replacing #1 with each item.
    """
    expander.skip_whitespace()
    clist_tokens = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    body = expander.parse_brace_as_tokens() or []

    items = _parse_clist_items(clist_tokens)

    # Build result: for each item, substitute #1 in body
    result_tokens = []
    for item in items:
        for tok in body:
            if tok.type == TokenType.PARAMETER and tok.value == "1":
                result_tokens.extend(item)
            else:
                result_tokens.append(tok)

    expander.push_tokens(result_tokens)
    return []


def clist_map_function_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_map_function:NN \l_my_clist \func
    Applies \func to each item in clist.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    func = expander.consume()

    if var and func:
        macro = expander.get_macro(var)
        clist_tokens = macro.definition if macro and macro.definition else []
        items = _parse_clist_items(clist_tokens)

        # Build result: \func{item1}\func{item2}...
        result_tokens = []
        for item in items:
            result_tokens.append(func)
            result_tokens.extend(_make_brace_tokens(item))

        expander.push_tokens(result_tokens)
    return []


def clist_put_right_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_put_right:Nn \l_my_clist {item}  ->  append item to clist
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    item = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        existing = macro.definition if macro and macro.definition else []

        # If existing is non-empty, add comma before new item
        if existing and _strip_whitespace_tokens(existing):
            new_def = existing + [Token(TokenType.CHARACTER, ",", catcode=Catcode.OTHER)] + item
        else:
            new_def = item

        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
            + _make_brace_tokens(new_def)
        )
    return []


def clist_put_left_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_put_left:Nn \l_my_clist {item}  ->  prepend item to clist
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    item = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        existing = macro.definition if macro and macro.definition else []

        # If existing is non-empty, add comma after new item
        if existing and _strip_whitespace_tokens(existing):
            new_def = item + [Token(TokenType.CHARACTER, ",", catcode=Catcode.OTHER)] + existing
        else:
            new_def = item

        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
            + _make_brace_tokens(new_def)
        )
    return []


def clist_count_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_count:N \l_my_clist  ->  number of items
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        macro = expander.get_macro(var)
        clist_tokens = macro.definition if macro and macro.definition else []
        items = _parse_clist_items(clist_tokens)
        return expander.convert_str_to_tokens(str(len(items)))
    return expander.convert_str_to_tokens("0")


def clist_count_n_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_count:n {a,b,c}  ->  number of items
    """
    expander.skip_whitespace()
    clist_tokens = expander.parse_brace_as_tokens() or []
    items = _parse_clist_items(clist_tokens)
    return expander.convert_str_to_tokens(str(len(items)))


def clist_use_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_use:Nnnn \l_my_clist {sep-two} {sep-mid} {sep-last}
    Joins clist items with separators.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    sep_two = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    sep_mid = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    sep_last = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        clist_tokens = macro.definition if macro and macro.definition else []
        items = _parse_clist_items(clist_tokens)

        result_tokens = []
        n = len(items)
        for i, item in enumerate(items):
            result_tokens.extend(item)
            if n == 2 and i == 0:
                result_tokens.extend(sep_two)
            elif n > 2:
                if i < n - 2:
                    result_tokens.extend(sep_mid)
                elif i == n - 2:
                    result_tokens.extend(sep_last)

        expander.push_tokens(result_tokens)
    return []


def clist_use_nn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_use:Nn \l_my_clist {separator}
    Joins all clist items with the same separator.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    sep = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        clist_tokens = macro.definition if macro and macro.definition else []
        items = _parse_clist_items(clist_tokens)

        result_tokens = []
        for i, item in enumerate(items):
            if i > 0:
                result_tokens.extend(sep)
            result_tokens.extend(item)

        expander.push_tokens(result_tokens)
    return []


def clist_if_empty_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_if_empty:NTF \l_my_clist {true} {false}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        clist_tokens = macro.definition if macro and macro.definition else []
        items = _parse_clist_items(clist_tokens)

        if len(items) == 0:
            expander.push_tokens(true_branch)
        else:
            expander.push_tokens(false_branch)
    else:
        expander.push_tokens(true_branch)
    return []


def clist_if_empty_T_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_if_empty:NT \l_my_clist {true}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        clist_tokens = macro.definition if macro and macro.definition else []
        items = _parse_clist_items(clist_tokens)

        if len(items) == 0:
            expander.push_tokens(true_branch)
    return []


def clist_if_empty_F_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_if_empty:NF \l_my_clist {false}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        clist_tokens = macro.definition if macro and macro.definition else []
        items = _parse_clist_items(clist_tokens)

        if len(items) > 0:
            expander.push_tokens(false_branch)
    return []


def clist_if_in_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_if_in:NnTF \l_my_clist {item} {true} {false}
    Check if item exists in clist.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    item_tokens = expander.parse_brace_as_tokens() or []
    item_str = "".join(t.value for t in item_tokens).strip()
    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        clist_tokens = macro.definition if macro and macro.definition else []
        items = _parse_clist_items(clist_tokens)

        found = False
        for item in items:
            if "".join(t.value for t in item).strip() == item_str:
                found = True
                break

        if found:
            expander.push_tokens(true_branch)
        else:
            expander.push_tokens(false_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def clist_item_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \clist_item:Nn \l_my_clist {index}
    Get item at 1-based index (negative counts from end).
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    idx_tokens = expander.parse_brace_as_tokens() or []
    idx_str = "".join(t.value for t in idx_tokens).strip()

    if var:
        try:
            idx = int(idx_str)
        except ValueError:
            return []

        macro = expander.get_macro(var)
        clist_tokens = macro.definition if macro and macro.definition else []
        items = _parse_clist_items(clist_tokens)

        if idx > 0 and idx <= len(items):
            expander.push_tokens(items[idx - 1])
        elif idx < 0 and abs(idx) <= len(items):
            expander.push_tokens(items[idx])
    return []


def register_clist_handlers(expander: ExpanderCore) -> None:
    """Register comma list handlers."""
    # Creation and clearing
    for name in ["\\clist_new:N", "\\clist_clear_new:N"]:
        expander.register_handler(name, clist_new_handler, is_global=True)
    for name in ["\\clist_clear:N", "\\clist_gclear:N"]:
        expander.register_handler(name, clist_clear_handler, is_global=True)

    # Setting
    for name in ["\\clist_set:Nn", "\\clist_set:Nx", "\\clist_set:No"]:
        expander.register_handler(name, clist_set_handler, is_global=True)
    for name in ["\\clist_gset:Nn", "\\clist_gset:Nx"]:
        expander.register_handler(name, clist_gset_handler, is_global=True)

    # Adding items
    for name in ["\\clist_put_right:Nn", "\\clist_put_right:Nx"]:
        expander.register_handler(name, clist_put_right_handler, is_global=True)
    for name in ["\\clist_put_left:Nn", "\\clist_put_left:Nx"]:
        expander.register_handler(name, clist_put_left_handler, is_global=True)

    # Mapping
    for name in ["\\clist_map_inline:Nn", "\\clist_map_inline:cn"]:
        expander.register_handler(name, clist_map_inline_handler, is_global=True)
    expander.register_handler("\\clist_map_inline:nn", clist_map_inline_n_handler, is_global=True)
    expander.register_handler(
        "\\clist_map_function:NN", clist_map_function_handler, is_global=True
    )

    # Counting
    for name in ["\\clist_count:N", "\\clist_count:c"]:
        expander.register_handler(name, clist_count_handler, is_global=True)
    expander.register_handler("\\clist_count:n", clist_count_n_handler, is_global=True)

    # Joining/using
    for name in ["\\clist_use:Nnnn", "\\clist_use:cnnn"]:
        expander.register_handler(name, clist_use_handler, is_global=True)
    for name in ["\\clist_use:Nn", "\\clist_use:cn"]:
        expander.register_handler(name, clist_use_nn_handler, is_global=True)

    # Conditionals
    expander.register_handler("\\clist_if_empty:NTF", clist_if_empty_TF_handler, is_global=True)
    expander.register_handler("\\clist_if_empty:NT", clist_if_empty_T_handler, is_global=True)
    expander.register_handler("\\clist_if_empty:NF", clist_if_empty_F_handler, is_global=True)
    expander.register_handler("\\clist_if_in:NnTF", clist_if_in_TF_handler, is_global=True)

    # Item access
    for name in ["\\clist_item:Nn", "\\clist_item:cn"]:
        expander.register_handler(name, clist_item_handler, is_global=True)
