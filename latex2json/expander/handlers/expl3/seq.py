r"""
expl3 sequence (seq) handlers.

Handles \seq_new:N, \seq_clear:N, \seq_put_right:Nn, \seq_map_inline:Nn,
\seq_use:Nnnn, and related functions.

Storage format: sequences store items as {item1}{item2}{item3}...
Each item is wrapped in braces for easy iteration.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
# (removed unused import)


def seq_new_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \seq_new:N \l_my_seq  ->  \def\l_my_seq{}
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


def seq_clear_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \seq_clear:N \l_my_seq  ->  \def\l_my_seq{}
    """
    return seq_new_handler(expander, _token)


def _make_brace_tokens(tokens: List[Token]) -> List[Token]:
    """Wrap tokens in braces (always, unlike _make_brace_tokens)."""
    return [
        Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
        *tokens,
        Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
    ]


def seq_put_right_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_put_right:Nn \l_my_seq {item}  ->  append {item} to sequence
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    item = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        existing = macro.definition if macro and macro.definition else []
        # Append new item wrapped in braces
        new_def = existing + _make_brace_tokens(item)
        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
            + _make_brace_tokens(new_def)
        )
    return []


def seq_gput_right_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_gput_right:Nn \l_my_seq {item}  ->  globally append {item} to sequence
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    item = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        existing = macro.definition if macro and macro.definition else []
        new_def = existing + _make_brace_tokens(item)
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "global"),
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
            ]
            + _make_brace_tokens(new_def)
        )
    return []


def seq_gput_right_cn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_gput_right:cn {seqname} {item}  ->  globally append {item} to constructed sequence
    """
    expander.skip_whitespace()
    name_tokens = expander.parse_brace_as_tokens() or []
    seq_name = "".join(t.value for t in name_tokens).strip()

    expander.skip_whitespace()
    item = expander.parse_brace_as_tokens() or []

    if seq_name:
        var = Token(TokenType.CONTROL_SEQUENCE, seq_name)
        macro = expander.get_macro(var)
        existing = macro.definition if macro and macro.definition else []
        new_def = existing + _make_brace_tokens(item)
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "global"),
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
            ]
            + _make_brace_tokens(new_def)
        )
    return []


def seq_put_left_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_put_left:Nn \l_my_seq {item}  ->  prepend {item} to sequence
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    item = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        existing = macro.definition if macro and macro.definition else []
        # Prepend new item wrapped in braces
        new_def = _make_brace_tokens(item) + existing
        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
            + _make_brace_tokens(new_def)
        )
    return []


def _parse_seq_items(tokens: List[Token]) -> List[List[Token]]:
    """
    Parse sequence tokens into individual items.
    Format: {item1}{item2}{item3}...
    Returns list of token lists, one per item.
    """
    items = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.catcode == Catcode.BEGIN_GROUP or (
            tok.type == TokenType.CHARACTER and tok.value == "{"
        ):
            # Found start of an item, collect until matching close
            depth = 1
            item_tokens = []
            i += 1
            while i < len(tokens) and depth > 0:
                t = tokens[i]
                if t.catcode == Catcode.BEGIN_GROUP or (
                    t.type == TokenType.CHARACTER and t.value == "{"
                ):
                    depth += 1
                    item_tokens.append(t)
                elif t.catcode == Catcode.END_GROUP or (
                    t.type == TokenType.CHARACTER and t.value == "}"
                ):
                    depth -= 1
                    if depth > 0:
                        item_tokens.append(t)
                else:
                    item_tokens.append(t)
                i += 1
            items.append(item_tokens)
        else:
            i += 1
    return items


def seq_map_inline_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_map_inline:Nn \l_my_seq {code with #1}
    Iterates over sequence items, replacing #1 with each item.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    body = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

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


def seq_map_function_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_map_function:NN \l_my_seq \func
    Applies \func to each item in sequence.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    func = expander.consume()

    if var and func:
        macro = expander.get_macro(var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

        # Build result: \func{item1}\func{item2}...
        result_tokens = []
        for item in items:
            result_tokens.append(func)
            result_tokens.extend(_make_brace_tokens(item))

        expander.push_tokens(result_tokens)
    return []


def seq_use_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \seq_use:Nnnn \l_my_seq {sep-two} {sep-mid} {sep-last}
    Joins sequence items with separators.
    - If 2 items: item1 <sep-two> item2
    - If 3+ items: item1 <sep-mid> item2 <sep-mid> ... <sep-last> itemN
    - If 0-1 items: just the item(s) with no separator
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
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

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


def seq_use_nn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_use:Nn \l_my_seq {separator}
    Joins all sequence items with the same separator.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    sep = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

        result_tokens = []
        for i, item in enumerate(items):
            if i > 0:
                result_tokens.extend(sep)
            result_tokens.extend(item)

        expander.push_tokens(result_tokens)
    return []


def seq_count_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \seq_count:N \l_my_seq  ->  number of items
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        macro = expander.get_macro(var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)
        return expander.convert_str_to_tokens(str(len(items)))
    return expander.convert_str_to_tokens("0")


def seq_if_empty_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_if_empty:NTF \l_my_seq {true} {false}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

        if len(items) == 0:
            expander.push_tokens(true_branch)
        else:
            expander.push_tokens(false_branch)
    else:
        expander.push_tokens(true_branch)
    return []


def seq_if_empty_T_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_if_empty:NT \l_my_seq {true}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

        if len(items) == 0:
            expander.push_tokens(true_branch)
    return []


def seq_if_empty_F_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_if_empty:NF \l_my_seq {false}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

        if len(items) > 0:
            expander.push_tokens(false_branch)
    return []


def seq_if_in_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_if_in:NnTF \l_my_seq {item} {true} {false}
    Tests if item is in the sequence.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    item_tokens = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

        item_str = "".join(t.value for t in item_tokens)
        found = any("".join(t.value for t in it) == item_str for it in items)

        if found:
            expander.push_tokens(true_branch)
        else:
            expander.push_tokens(false_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def seq_if_in_T_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_if_in:NnT \l_my_seq {item} {true}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    item_tokens = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

        item_str = "".join(t.value for t in item_tokens)
        found = any("".join(t.value for t in it) == item_str for it in items)

        if found:
            expander.push_tokens(true_branch)
    return []


def seq_if_in_F_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_if_in:NnF \l_my_seq {item} {false}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    item_tokens = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

        item_str = "".join(t.value for t in item_tokens)
        found = any("".join(t.value for t in it) == item_str for it in items)

        if not found:
            expander.push_tokens(false_branch)
    return []


def seq_get_left_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_get_left:NN \l_my_seq \l_item_tl
    Gets the leftmost item without removing it.
    """
    expander.skip_whitespace()
    seq_var = expander.consume()
    expander.skip_whitespace()
    item_var = expander.consume()

    if seq_var and item_var:
        macro = expander.get_macro(seq_var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

        if items:
            # Set the item variable to the first item
            expander.push_tokens(
                [Token(TokenType.CONTROL_SEQUENCE, "def"), item_var]
                + _make_brace_tokens(items[0])
            )
        else:
            # Set to empty
            expander.push_tokens(
                [
                    Token(TokenType.CONTROL_SEQUENCE, "def"),
                    item_var,
                    Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
                    Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
                ]
            )
    return []


def seq_pop_left_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_pop_left:NN \l_my_seq \l_item_tl
    Pops the leftmost item and stores it.
    """
    expander.skip_whitespace()
    seq_var = expander.consume()
    expander.skip_whitespace()
    item_var = expander.consume()

    if seq_var and item_var:
        macro = expander.get_macro(seq_var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

        result_tokens = []
        if items:
            # Set the item variable to the first item
            result_tokens.extend(
                [Token(TokenType.CONTROL_SEQUENCE, "def"), item_var]
                + _make_brace_tokens(items[0])
            )
            # Rebuild sequence without first item
            new_seq_tokens = []
            for item in items[1:]:
                new_seq_tokens.extend(_make_brace_tokens(item))
            result_tokens.extend(
                [Token(TokenType.CONTROL_SEQUENCE, "def"), seq_var]
                + _make_brace_tokens(new_seq_tokens)
            )
        else:
            # Set item to empty
            result_tokens.extend(
                [
                    Token(TokenType.CONTROL_SEQUENCE, "def"),
                    item_var,
                    Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
                    Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
                ]
            )
        expander.push_tokens(result_tokens)
    return []


def seq_item_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_item:Nn \l_my_seq {index}
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
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

        if idx > 0 and idx <= len(items):
            expander.push_tokens(items[idx - 1])
        elif idx < 0 and abs(idx) <= len(items):
            expander.push_tokens(items[idx])
    return []


def seq_pop_right_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_pop_right:NN \l_my_seq \l_item_tl
    Pops the rightmost item and stores it.
    """
    expander.skip_whitespace()
    seq_var = expander.consume()
    expander.skip_whitespace()
    item_var = expander.consume()

    if seq_var and item_var:
        macro = expander.get_macro(seq_var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

        result_tokens = []
        if items:
            # Set the item variable to the last item
            result_tokens.extend(
                [Token(TokenType.CONTROL_SEQUENCE, "def"), item_var]
                + _make_brace_tokens(items[-1])
            )
            # Rebuild sequence without last item
            new_seq_tokens = []
            for item in items[:-1]:
                new_seq_tokens.extend(_make_brace_tokens(item))
            result_tokens.extend(
                [Token(TokenType.CONTROL_SEQUENCE, "def"), seq_var]
                + _make_brace_tokens(new_seq_tokens)
            )
        else:
            # Set item to empty
            result_tokens.extend(
                [
                    Token(TokenType.CONTROL_SEQUENCE, "def"),
                    item_var,
                    Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
                    Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
                ]
            )
        expander.push_tokens(result_tokens)
    return []


def seq_get_right_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_get_right:NN \l_my_seq \l_item_tl
    Gets the rightmost item without removing it.
    """
    expander.skip_whitespace()
    seq_var = expander.consume()
    expander.skip_whitespace()
    item_var = expander.consume()

    if seq_var and item_var:
        macro = expander.get_macro(seq_var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

        if items:
            # Set the item variable to the last item
            expander.push_tokens(
                [Token(TokenType.CONTROL_SEQUENCE, "def"), item_var]
                + _make_brace_tokens(items[-1])
            )
        else:
            # Set to empty
            expander.push_tokens(
                [
                    Token(TokenType.CONTROL_SEQUENCE, "def"),
                    item_var,
                    Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
                    Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP),
                ]
            )
    return []


def seq_gput_left_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_gput_left:Nn \l_my_seq {item}  ->  globally prepend {item} to sequence
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    item = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        existing = macro.definition if macro and macro.definition else []
        # Prepend new item wrapped in braces
        new_def = _make_brace_tokens(item) + existing
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "global"),
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
            ]
            + _make_brace_tokens(new_def)
        )
    return []


def seq_gremove_duplicates_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_gremove_duplicates:N \g_my_seq
    Globally removes duplicate items from sequence, keeping first occurrence.
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        macro = expander.get_macro(var)
        seq_tokens = macro.definition if macro and macro.definition else []
        items = _parse_seq_items(seq_tokens)

        # Remove duplicates while preserving order
        seen = []
        unique_items = []
        for item in items:
            item_str = "".join(t.value for t in item)
            if item_str not in seen:
                seen.append(item_str)
                unique_items.append(item)

        # Rebuild sequence
        new_def = []
        for item in unique_items:
            new_def.extend(_make_brace_tokens(item))

        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "global"),
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
            ]
            + _make_brace_tokens(new_def)
        )
    return []


def seq_gconcat_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_gconcat:NNN \g_result_seq \l_seq_a \l_seq_b
    Globally concatenates two sequences into the first.
    """
    expander.skip_whitespace()
    result_var = expander.consume()
    expander.skip_whitespace()
    seq_a_var = expander.consume()
    expander.skip_whitespace()
    seq_b_var = expander.consume()

    if result_var and seq_a_var and seq_b_var:
        macro_a = expander.get_macro(seq_a_var)
        tokens_a = macro_a.definition if macro_a and macro_a.definition else []

        macro_b = expander.get_macro(seq_b_var)
        tokens_b = macro_b.definition if macro_b and macro_b.definition else []

        # Concatenate the sequences
        new_def = tokens_a + tokens_b

        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "global"),
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                result_var,
            ]
            + _make_brace_tokens(new_def)
        )
    return []


def seq_set_from_clist_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_set_from_clist:Nn \l_my_seq {a,b,c}
    Creates a sequence from a comma-separated list.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    clist_tokens = expander.parse_brace_as_tokens() or []

    if var:
        # Parse comma-separated items
        items = _parse_clist_items(clist_tokens)
        # Build sequence format: {item1}{item2}...
        new_def = []
        for item in items:
            new_def.extend(_make_brace_tokens(item))

        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
            + _make_brace_tokens(new_def)
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
            if current_item:
                items.append(_strip_whitespace_tokens(current_item))
            current_item = []
        else:
            current_item.append(tok)

    # Don't forget the last item
    if current_item:
        items.append(_strip_whitespace_tokens(current_item))

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


def seq_set_split_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \seq_set_split:Nnn \l_my_seq {separator} {text}
    \seq_set_split:NnV \l_my_seq {separator} \l_my_tl
    Splits text by separator and creates a sequence from the parts.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    sep_tokens = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    # Third argument could be braced text or a variable (for V variant)
    text_tokens = expander.parse_brace_as_tokens()
    if text_tokens is None:
        # V variant - consume the variable and get its value
        text_var = expander.consume()
        if text_var:
            macro = expander.get_macro(text_var)
            text_tokens = macro.definition if macro and macro.definition else []
        else:
            text_tokens = []

    if var:
        sep_str = "".join(t.value for t in sep_tokens)
        text_str = "".join(t.value for t in text_tokens)

        # Split the text by separator
        if sep_str:
            parts = text_str.split(sep_str)
        else:
            # Empty separator: split into individual characters
            parts = list(text_str) if text_str else []

        # Build sequence format: {part1}{part2}...
        new_def = []
        for part in parts:
            part_tokens = expander.convert_str_to_tokens(part)
            new_def.extend(_make_brace_tokens(part_tokens))

        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
            + _make_brace_tokens(new_def)
        )
    return []


def register_seq_handlers(expander: ExpanderCore) -> None:
    """Register sequence handlers."""
    # Creation and clearing
    for name in ["\\seq_new:N", "\\seq_clear_new:N"]:
        expander.register_handler(name, seq_new_handler, is_global=True)
    for name in ["\\seq_clear:N", "\\seq_gclear:N"]:
        expander.register_handler(name, seq_clear_handler, is_global=True)

    # Adding items
    for name in ["\\seq_put_right:Nn", "\\seq_put_right:Nx", "\\seq_put_right:No"]:
        expander.register_handler(name, seq_put_right_handler, is_global=True)
    for name in ["\\seq_gput_right:Nn", "\\seq_gput_right:Nx"]:
        expander.register_handler(name, seq_gput_right_handler, is_global=True)
    for name in ["\\seq_gput_right:cn", "\\seq_gput_right:cx"]:
        expander.register_handler(name, seq_gput_right_cn_handler, is_global=True)
    for name in ["\\seq_put_left:Nn", "\\seq_put_left:Nx"]:
        expander.register_handler(name, seq_put_left_handler, is_global=True)

    # Mapping
    for name in ["\\seq_map_inline:Nn", "\\seq_map_inline:cn"]:
        expander.register_handler(name, seq_map_inline_handler, is_global=True)
    expander.register_handler(
        "\\seq_map_function:NN", seq_map_function_handler, is_global=True
    )

    # Joining/using
    for name in ["\\seq_use:Nnnn", "\\seq_use:cnnn"]:
        expander.register_handler(name, seq_use_handler, is_global=True)
    for name in ["\\seq_use:Nn", "\\seq_use:cn"]:
        expander.register_handler(name, seq_use_nn_handler, is_global=True)

    # Counting
    for name in ["\\seq_count:N", "\\seq_count:c"]:
        expander.register_handler(name, seq_count_handler, is_global=True)

    # Conditionals - empty
    expander.register_handler("\\seq_if_empty:NTF", seq_if_empty_TF_handler, is_global=True)
    expander.register_handler("\\seq_if_empty:NT", seq_if_empty_T_handler, is_global=True)
    expander.register_handler("\\seq_if_empty:NF", seq_if_empty_F_handler, is_global=True)

    # Conditionals - in (membership test)
    expander.register_handler("\\seq_if_in:NnTF", seq_if_in_TF_handler, is_global=True)
    expander.register_handler("\\seq_if_in:NnT", seq_if_in_T_handler, is_global=True)
    expander.register_handler("\\seq_if_in:NnF", seq_if_in_F_handler, is_global=True)

    # Getting items
    expander.register_handler("\\seq_get_left:NN", seq_get_left_handler, is_global=True)
    expander.register_handler("\\seq_get_right:NN", seq_get_right_handler, is_global=True)
    expander.register_handler("\\seq_pop_left:NN", seq_pop_left_handler, is_global=True)
    for name in ["\\seq_item:Nn", "\\seq_item:cn"]:
        expander.register_handler(name, seq_item_handler, is_global=True)

    # Global put left
    for name in ["\\seq_gput_left:Nn", "\\seq_gput_left:NV", "\\seq_gput_left:Nx"]:
        expander.register_handler(name, seq_gput_left_handler, is_global=True)

    # Remove duplicates
    expander.register_handler(
        "\\seq_gremove_duplicates:N", seq_gremove_duplicates_handler, is_global=True
    )

    # Concatenation
    expander.register_handler("\\seq_gconcat:NNN", seq_gconcat_handler, is_global=True)

    # From clist
    for name in ["\\seq_set_from_clist:Nn", "\\seq_set_from_clist:Nx"]:
        expander.register_handler(name, seq_set_from_clist_handler, is_global=True)

    # Pop right
    expander.register_handler("\\seq_pop_right:NN", seq_pop_right_handler, is_global=True)

    # Set split
    for name in ["\\seq_set_split:Nnn", "\\seq_set_split:NnV"]:
        expander.register_handler(name, seq_set_split_handler, is_global=True)
