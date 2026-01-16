"""
expl3 property list (prop) handlers.

Handles \prop_new:N, \prop_put:Nnn, \prop_get:NnN, \prop_if_in:NnTF,
and related functions.

Storage format: property lists store key-value pairs as {key1}{val1}{key2}{val2}...
Each key and value is wrapped in braces for easy iteration.
"""

from typing import List, Optional, Tuple

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


def prop_new_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \prop_new:N \l_my_prop  ->  \def\l_my_prop{}
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


def prop_clear_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \prop_clear:N \l_my_prop  ->  \def\l_my_prop{}
    """
    return prop_new_handler(expander, _token)


def _parse_prop_items(tokens: List[Token]) -> List[Tuple[List[Token], List[Token]]]:
    """
    Parse property list tokens into key-value pairs.
    Format: {key1}{val1}{key2}{val2}...
    Returns list of (key_tokens, value_tokens) tuples.
    """
    items = []
    i = 0

    def parse_braced_group(start_idx: int) -> Tuple[List[Token], int]:
        """Parse a single braced group starting at index."""
        if start_idx >= len(tokens):
            return [], start_idx

        tok = tokens[start_idx]
        if not (tok.catcode == Catcode.BEGIN_GROUP or
                (tok.type == TokenType.CHARACTER and tok.value == "{")):
            return [], start_idx

        depth = 1
        group_tokens = []
        idx = start_idx + 1

        while idx < len(tokens) and depth > 0:
            t = tokens[idx]
            if t.catcode == Catcode.BEGIN_GROUP or (
                t.type == TokenType.CHARACTER and t.value == "{"
            ):
                depth += 1
                group_tokens.append(t)
            elif t.catcode == Catcode.END_GROUP or (
                t.type == TokenType.CHARACTER and t.value == "}"
            ):
                depth -= 1
                if depth > 0:
                    group_tokens.append(t)
            else:
                group_tokens.append(t)
            idx += 1

        return group_tokens, idx

    while i < len(tokens):
        tok = tokens[i]
        if tok.catcode == Catcode.BEGIN_GROUP or (
            tok.type == TokenType.CHARACTER and tok.value == "{"
        ):
            # Parse key
            key_tokens, i = parse_braced_group(i)
            # Skip whitespace
            while i < len(tokens) and tokens[i].value.isspace():
                i += 1
            # Parse value
            if i < len(tokens):
                val_tokens, i = parse_braced_group(i)
                items.append((key_tokens, val_tokens))
        else:
            i += 1

    return items


def _tokens_to_str(tokens: List[Token]) -> str:
    """Convert tokens to string for key comparison."""
    return "".join(t.value for t in tokens).strip()


def prop_put_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \prop_put:Nnn \l_my_prop {key} {value}
    Sets key to value in property list (adds or updates).
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    key = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    value = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        prop_tokens = macro.definition if macro and macro.definition else []
        items = _parse_prop_items(prop_tokens)

        key_str = _tokens_to_str(key)

        # Check if key exists and update, or add new
        found = False
        new_items = []
        for k, v in items:
            if _tokens_to_str(k) == key_str:
                new_items.append((key, value))
                found = True
            else:
                new_items.append((k, v))

        if not found:
            new_items.append((key, value))

        # Rebuild property list
        new_def = []
        for k, v in new_items:
            new_def.extend(_make_brace_tokens(k))
            new_def.extend(_make_brace_tokens(v))

        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
            + _make_brace_tokens(new_def)
        )
    return []


def prop_gput_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \prop_gput:Nnn \g_my_prop {key} {value}
    Globally sets key to value in property list.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    key = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    value = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        prop_tokens = macro.definition if macro and macro.definition else []
        items = _parse_prop_items(prop_tokens)

        key_str = _tokens_to_str(key)

        found = False
        new_items = []
        for k, v in items:
            if _tokens_to_str(k) == key_str:
                new_items.append((key, value))
                found = True
            else:
                new_items.append((k, v))

        if not found:
            new_items.append((key, value))

        new_def = []
        for k, v in new_items:
            new_def.extend(_make_brace_tokens(k))
            new_def.extend(_make_brace_tokens(v))

        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "global"),
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                var,
            ]
            + _make_brace_tokens(new_def)
        )
    return []


def prop_get_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \prop_get:NnN \l_my_prop {key} \l_value_tl
    Gets value for key and stores in token list variable.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    key = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    result_var = expander.consume()

    if var and result_var:
        macro = expander.get_macro(var)
        prop_tokens = macro.definition if macro and macro.definition else []
        items = _parse_prop_items(prop_tokens)

        key_str = _tokens_to_str(key)

        # Find value for key
        found_value = []
        for k, v in items:
            if _tokens_to_str(k) == key_str:
                found_value = v
                break

        # Set result variable
        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), result_var]
            + _make_brace_tokens(found_value)
        )
    return []


def prop_item_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \prop_item:Nn \l_my_prop {key}
    Returns value for key directly (expandable).
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    key = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        prop_tokens = macro.definition if macro and macro.definition else []
        items = _parse_prop_items(prop_tokens)

        key_str = _tokens_to_str(key)

        # Find value for key
        for k, v in items:
            if _tokens_to_str(k) == key_str:
                expander.push_tokens(v)
                break
    return []


def prop_remove_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \prop_remove:Nn \l_my_prop {key}
    Removes key from property list.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    key = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        prop_tokens = macro.definition if macro and macro.definition else []
        items = _parse_prop_items(prop_tokens)

        key_str = _tokens_to_str(key)

        # Filter out the key
        new_items = [(k, v) for k, v in items if _tokens_to_str(k) != key_str]

        # Rebuild property list
        new_def = []
        for k, v in new_items:
            new_def.extend(_make_brace_tokens(k))
            new_def.extend(_make_brace_tokens(v))

        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
            + _make_brace_tokens(new_def)
        )
    return []


def prop_if_in_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \prop_if_in:NnTF \l_my_prop {key} {true} {false}
    Check if key exists in property list.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    key = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        prop_tokens = macro.definition if macro and macro.definition else []
        items = _parse_prop_items(prop_tokens)

        key_str = _tokens_to_str(key)

        found = any(_tokens_to_str(k) == key_str for k, _ in items)

        if found:
            expander.push_tokens(true_branch)
        else:
            expander.push_tokens(false_branch)
    else:
        expander.push_tokens(false_branch)
    return []


def prop_if_in_T_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \prop_if_in:NnT \l_my_prop {key} {true}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    key = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        prop_tokens = macro.definition if macro and macro.definition else []
        items = _parse_prop_items(prop_tokens)

        key_str = _tokens_to_str(key)

        if any(_tokens_to_str(k) == key_str for k, _ in items):
            expander.push_tokens(true_branch)
    return []


def prop_if_in_F_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \prop_if_in:NnF \l_my_prop {key} {false}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    key = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        prop_tokens = macro.definition if macro and macro.definition else []
        items = _parse_prop_items(prop_tokens)

        key_str = _tokens_to_str(key)

        if not any(_tokens_to_str(k) == key_str for k, _ in items):
            expander.push_tokens(false_branch)
    return []


def prop_if_empty_TF_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \prop_if_empty:NTF \l_my_prop {true} {false}
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    true_branch = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()
    false_branch = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        prop_tokens = macro.definition if macro and macro.definition else []
        items = _parse_prop_items(prop_tokens)

        if len(items) == 0:
            expander.push_tokens(true_branch)
        else:
            expander.push_tokens(false_branch)
    else:
        expander.push_tokens(true_branch)
    return []


def prop_count_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \prop_count:N \l_my_prop  ->  number of key-value pairs
    """
    expander.skip_whitespace()
    var = expander.consume()

    if var:
        macro = expander.get_macro(var)
        prop_tokens = macro.definition if macro and macro.definition else []
        items = _parse_prop_items(prop_tokens)
        return expander.convert_str_to_tokens(str(len(items)))
    return expander.convert_str_to_tokens("0")


def prop_map_inline_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \prop_map_inline:Nn \l_my_prop {code with #1 and #2}
    Iterates over property list, replacing #1 with key and #2 with value.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    body = expander.parse_brace_as_tokens() or []

    if var:
        macro = expander.get_macro(var)
        prop_tokens = macro.definition if macro and macro.definition else []
        items = _parse_prop_items(prop_tokens)

        # Build result: for each key-value pair, substitute #1 and #2 in body
        result_tokens = []
        for key, value in items:
            for tok in body:
                if tok.type == TokenType.PARAMETER:
                    if tok.value == "1":
                        result_tokens.extend(key)
                    elif tok.value == "2":
                        result_tokens.extend(value)
                    else:
                        result_tokens.append(tok)
                else:
                    result_tokens.append(tok)

        expander.push_tokens(result_tokens)
    return []


def prop_map_function_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \prop_map_function:NN \l_my_prop \func
    Applies \func{key}{value} to each pair.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    func = expander.consume()

    if var and func:
        macro = expander.get_macro(var)
        prop_tokens = macro.definition if macro and macro.definition else []
        items = _parse_prop_items(prop_tokens)

        # Build result: \func{key1}{val1}\func{key2}{val2}...
        result_tokens = []
        for key, value in items:
            result_tokens.append(func)
            result_tokens.extend(_make_brace_tokens(key))
            result_tokens.extend(_make_brace_tokens(value))

        expander.push_tokens(result_tokens)
    return []


def prop_set_from_keyval_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \prop_set_from_keyval:Nn \l_my_prop {key1=val1, key2=val2}
    Sets property list from key=value format.
    """
    expander.skip_whitespace()
    var = expander.consume()
    expander.skip_whitespace()
    keyval_tokens = expander.parse_brace_as_tokens() or []

    if var:
        # Parse key=value pairs
        items = _parse_keyval(keyval_tokens)

        # Build property list format
        new_def = []
        for key, value in items:
            new_def.extend(_make_brace_tokens(key))
            new_def.extend(_make_brace_tokens(value))

        expander.push_tokens(
            [Token(TokenType.CONTROL_SEQUENCE, "def"), var]
            + _make_brace_tokens(new_def)
        )
    return []


def _parse_keyval(tokens: List[Token]) -> List[Tuple[List[Token], List[Token]]]:
    """
    Parse key=value tokens into list of (key, value) tuples.
    Handles nested braces and commas correctly.
    """
    items = []
    current = []
    depth = 0

    for tok in tokens:
        if tok.catcode == Catcode.BEGIN_GROUP or (
            tok.type == TokenType.CHARACTER and tok.value == "{"
        ):
            depth += 1
            current.append(tok)
        elif tok.catcode == Catcode.END_GROUP or (
            tok.type == TokenType.CHARACTER and tok.value == "}"
        ):
            depth -= 1
            current.append(tok)
        elif tok.value == "," and depth == 0:
            # End of current key=value pair
            if current:
                kv = _split_keyval_pair(current)
                if kv:
                    items.append(kv)
            current = []
        else:
            current.append(tok)

    # Don't forget the last pair
    if current:
        kv = _split_keyval_pair(current)
        if kv:
            items.append(kv)

    return items


def _split_keyval_pair(tokens: List[Token]) -> Optional[Tuple[List[Token], List[Token]]]:
    """Split key=value tokens into (key, value) tuple."""
    # Find the = sign at depth 0
    depth = 0
    eq_idx = -1

    for i, tok in enumerate(tokens):
        if tok.catcode == Catcode.BEGIN_GROUP or (
            tok.type == TokenType.CHARACTER and tok.value == "{"
        ):
            depth += 1
        elif tok.catcode == Catcode.END_GROUP or (
            tok.type == TokenType.CHARACTER and tok.value == "}"
        ):
            depth -= 1
        elif tok.value == "=" and depth == 0:
            eq_idx = i
            break

    if eq_idx == -1:
        # No = found, skip this pair
        return None

    key = _strip_whitespace_tokens(tokens[:eq_idx])
    value = _strip_whitespace_tokens(tokens[eq_idx + 1:])

    if not key:
        return None

    return (key, value)


def _strip_whitespace_tokens(tokens: List[Token]) -> List[Token]:
    """Strip leading and trailing whitespace tokens."""
    start = 0
    while start < len(tokens) and tokens[start].value.isspace():
        start += 1
    end = len(tokens)
    while end > start and tokens[end - 1].value.isspace():
        end -= 1
    return tokens[start:end]


def register_prop_handlers(expander: ExpanderCore) -> None:
    """Register property list handlers."""
    # Creation and clearing
    for name in ["\\prop_new:N", "\\prop_clear_new:N"]:
        expander.register_handler(name, prop_new_handler, is_global=True)
    for name in ["\\prop_clear:N", "\\prop_gclear:N"]:
        expander.register_handler(name, prop_clear_handler, is_global=True)

    # Putting values
    for name in ["\\prop_put:Nnn", "\\prop_put:NnV", "\\prop_put:Nnx"]:
        expander.register_handler(name, prop_put_handler, is_global=True)
    for name in ["\\prop_gput:Nnn", "\\prop_gput:NnV"]:
        expander.register_handler(name, prop_gput_handler, is_global=True)

    # Getting values
    for name in ["\\prop_get:NnN", "\\prop_get:NnNTF"]:
        expander.register_handler(name, prop_get_handler, is_global=True)
    for name in ["\\prop_item:Nn", "\\prop_item:cn"]:
        expander.register_handler(name, prop_item_handler, is_global=True)

    # Removing
    for name in ["\\prop_remove:Nn", "\\prop_gremove:Nn"]:
        expander.register_handler(name, prop_remove_handler, is_global=True)

    # Conditionals
    expander.register_handler("\\prop_if_in:NnTF", prop_if_in_TF_handler, is_global=True)
    expander.register_handler("\\prop_if_in:NnT", prop_if_in_T_handler, is_global=True)
    expander.register_handler("\\prop_if_in:NnF", prop_if_in_F_handler, is_global=True)
    expander.register_handler("\\prop_if_empty:NTF", prop_if_empty_TF_handler, is_global=True)

    # Counting
    for name in ["\\prop_count:N", "\\prop_count:c"]:
        expander.register_handler(name, prop_count_handler, is_global=True)

    # Mapping
    for name in ["\\prop_map_inline:Nn", "\\prop_map_inline:cn"]:
        expander.register_handler(name, prop_map_inline_handler, is_global=True)
    expander.register_handler(
        "\\prop_map_function:NN", prop_map_function_handler, is_global=True
    )

    # From keyval
    for name in ["\\prop_set_from_keyval:Nn", "\\prop_set_from_keyval:Nx"]:
        expander.register_handler(name, prop_set_from_keyval_handler, is_global=True)
