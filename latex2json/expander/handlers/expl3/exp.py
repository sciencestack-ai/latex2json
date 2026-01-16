"""
expl3 expansion control (exp) handlers.

Handles \exp_args:N..., \exp_not:n, \exp_not:N, etc.
"""

from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import wrap_tokens_in_braces


# =============================================================================
# \exp_not:... - Expansion prevention
# =============================================================================


def exp_not_n_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \exp_not:n {tokens}  ->  tokens without expansion (like \unexpanded)
    """
    expander.skip_whitespace()
    tokens = expander.parse_brace_as_tokens() or []
    # Return directly without pushing - prevents further expansion
    return tokens


def exp_not_N_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \exp_not:N \cmd  ->  \cmd without expansion (like \noexpand)
    """
    expander.skip_whitespace()
    tok = expander.consume()
    if tok:
        return [tok]
    return []


def exp_not_c_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \exp_not:c {name}  ->  \name without expansion
    """
    expander.skip_whitespace()
    name_tokens = expander.parse_brace_as_tokens() or []
    name = "".join(t.value for t in name_tokens)
    if name:
        return [Token(TokenType.CONTROL_SEQUENCE, name)]
    return []


# =============================================================================
# \exp_args:N... - Argument expansion control
# =============================================================================


def exp_args_No_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \exp_args:No \cmd {arg}  ->  expand arg once, then \cmd{expanded}

    We approximate "once" with full expansion since single-step is complex.
    """
    expander.skip_whitespace()
    cmd = expander.consume()
    expander.skip_whitespace()
    arg = expander.parse_brace_as_tokens(expand=True)

    if cmd and arg is not None:
        expander.push_tokens([cmd] + wrap_tokens_in_braces(arg))
    elif cmd:
        expander.push_tokens([cmd])
    return []


def exp_args_Nx_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \exp_args:Nx \cmd {arg}  ->  fully expand arg, then \cmd{expanded}
    """
    expander.skip_whitespace()
    cmd = expander.consume()
    expander.skip_whitespace()
    arg = expander.parse_brace_as_tokens(expand=True)

    if cmd and arg is not None:
        expander.push_tokens([cmd] + wrap_tokens_in_braces(arg))
    elif cmd:
        expander.push_tokens([cmd])
    return []


def exp_args_NV_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \exp_args:NV \cmd \var  ->  get value of \var, then \cmd{value}
    """
    expander.skip_whitespace()
    cmd = expander.consume()
    expander.skip_whitespace()
    var = expander.consume()

    if cmd and var:
        # Get the variable's definition
        macro = expander.get_macro(var)
        if macro and macro.definition:
            expander.push_tokens([cmd] + wrap_tokens_in_braces(macro.definition))
        else:
            # No definition, just pass empty
            expander.push_tokens([cmd] + wrap_tokens_in_braces([]))
    elif cmd:
        expander.push_tokens([cmd])
    return []


def exp_args_Nv_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \exp_args:Nv \cmd {varname}  ->  construct \varname, get value, then \cmd{value}
    """
    expander.skip_whitespace()
    cmd = expander.consume()
    expander.skip_whitespace()
    varname_tokens = expander.parse_brace_as_tokens() or []
    varname = "".join(t.value for t in varname_tokens)

    if cmd and varname:
        macro = expander.get_macro("\\" + varname)
        if macro and macro.definition:
            expander.push_tokens([cmd] + wrap_tokens_in_braces(macro.definition))
        else:
            expander.push_tokens([cmd] + wrap_tokens_in_braces([]))
    elif cmd:
        expander.push_tokens([cmd])
    return []


def exp_args_Nc_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \exp_args:Nc \cmd {name}  ->  construct \name, then \cmd \name

    Like \csname but for exp_args.
    """
    expander.skip_whitespace()
    cmd = expander.consume()
    expander.skip_whitespace()
    name_tokens = expander.parse_brace_as_tokens() or []
    name = "".join(t.value for t in name_tokens)

    if cmd and name:
        cs_token = Token(TokenType.CONTROL_SEQUENCE, name)
        expander.push_tokens([cmd, cs_token])
    elif cmd:
        expander.push_tokens([cmd])
    return []


def exp_args_Noo_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \exp_args:Noo \cmd {arg1} {arg2}  ->  expand both args once
    """
    expander.skip_whitespace()
    cmd = expander.consume()
    args = expander.parse_braced_blocks(N_blocks=2, expand=True)

    if cmd:
        result = [cmd]
        for arg in args:
            result.extend(wrap_tokens_in_braces(arg))
        expander.push_tokens(result)
    return []


def exp_args_NNx_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \exp_args:NNx \cmd \tok {arg}  ->  pass \tok as is, expand arg
    """
    expander.skip_whitespace()
    cmd = expander.consume()
    expander.skip_whitespace()
    tok = expander.consume()
    expander.skip_whitespace()
    arg = expander.parse_brace_as_tokens(expand=True)

    if cmd:
        result = [cmd]
        if tok:
            result.append(tok)
        if arg is not None:
            result.extend(wrap_tokens_in_braces(arg))
        expander.push_tokens(result)
    return []


def exp_args_NNV_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \exp_args:NNV \cmd \tok \var  ->  pass \tok as is, get value of \var
    """
    expander.skip_whitespace()
    cmd = expander.consume()
    expander.skip_whitespace()
    tok = expander.consume()
    expander.skip_whitespace()
    var = expander.consume()

    if cmd:
        result = [cmd]
        if tok:
            result.append(tok)
        if var:
            macro = expander.get_macro(var)
            if macro and macro.definition:
                result.extend(wrap_tokens_in_braces(macro.definition))
            else:
                result.extend(wrap_tokens_in_braces([]))
        expander.push_tokens(result)
    return []


def register_exp_handlers(expander: ExpanderCore) -> None:
    """Register expansion control handlers."""
    # Expansion prevention
    expander.register_handler("\\exp_not:n", exp_not_n_handler, is_global=True)
    expander.register_handler("\\exp_not:N", exp_not_N_handler, is_global=True)
    expander.register_handler("\\exp_not:c", exp_not_c_handler, is_global=True)

    # Single expanded arg
    for name in ["\\exp_args:No", "\\exp_args:Nf"]:
        expander.register_handler(name, exp_args_No_handler, is_global=True)
    expander.register_handler("\\exp_args:Nx", exp_args_Nx_handler, is_global=True)
    expander.register_handler("\\exp_args:NV", exp_args_NV_handler, is_global=True)
    expander.register_handler("\\exp_args:Nv", exp_args_Nv_handler, is_global=True)
    expander.register_handler("\\exp_args:Nc", exp_args_Nc_handler, is_global=True)

    # Two expanded args
    for name in ["\\exp_args:Noo", "\\exp_args:Nxx", "\\exp_args:Nff"]:
        expander.register_handler(name, exp_args_Noo_handler, is_global=True)

    # Mixed: N + expanded
    for name in ["\\exp_args:NNo", "\\exp_args:NNx", "\\exp_args:NNf"]:
        expander.register_handler(name, exp_args_NNx_handler, is_global=True)
    expander.register_handler("\\exp_args:NNV", exp_args_NNV_handler, is_global=True)
