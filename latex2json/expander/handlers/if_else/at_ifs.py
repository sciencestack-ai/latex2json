from typing import List, Optional
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token
from latex2json.expander.expander_core import ExpanderCore


def if_star_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""
    Evaluates \ifstar condition by checking if next token is an asterisk.
    Returns (True, None) if next token is *, (False, None) if not,
    or (None, error_msg) if there's an error.
    """
    blocks = expander.parse_braced_blocks(2)

    if len(blocks) != 2:
        expander.logger.warning("Warning: \\@ifstar expects 2 blocks")
        return None

    has_star = expander.parse_asterisk()
    block = blocks[0] if has_star else blocks[1]
    expander.push_tokens(block)
    return []


def if_nextchar_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""
    Evaluates \ifnextchar condition by checking if next token is a given character.
    Returns (True, None) if next token is the character, (False, None) if not,
    or (None, error_msg) if there's an error.
    """
    expander.skip_whitespace()
    tok1 = expander.consume()
    if tok1 is None:
        expander.logger.warning("Warning: \\@ifnextchar expects a char")
        return None

    expander.skip_whitespace()
    blocks = expander.parse_braced_blocks(2)
    if len(blocks) != 2:
        expander.logger.warning("Warning: \\@ifnextchar expects 2 blocks")
        return None

    expander.skip_whitespace()
    tok2 = expander.peek()
    if tok2 is None:
        expander.logger.warning(
            "Warning: \\@ifnextchar expects a token after \\@ifnextchar[{}{}"
        )
        return None

    char1 = expander.convert_token_to_char_token(tok1)
    char2 = expander.convert_token_to_char_token(tok2)

    is_equal = False
    if char1 and char2:
        is_equal = char1 == char2

    block = blocks[0] if is_equal else blocks[1]
    expander.push_tokens(block)
    return []


def if_mathmode_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    blocks = expander.parse_braced_blocks(2)
    if len(blocks) != 2:
        expander.logger.warning("Warning: \\@ifmmode expects 2 blocks")
        return None

    block = blocks[0] if expander.state.is_math_mode else blocks[1]
    expander.push_tokens(block)
    return []


def if_undefined_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    command_name = expander.parse_brace_name()
    blocks = expander.parse_braced_blocks(2)
    if len(blocks) != 2:
        expander.logger.warning("Warning: \\@ifundefined expects 3 blocks")
        return None

    is_undefined = True
    if command_name:
        is_undefined = expander.get_macro(command_name) is None
    block = blocks[0] if is_undefined else blocks[1]
    expander.push_tokens(block)
    return []


def ifdefinable_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    tokens = expander.parse_immediate_token()
    if tokens is None or len(tokens) < 1:
        expander.logger.warning("Warning: \\@ifdefinable expects a token")
        return None

    command_name = tokens[0].value
    is_definable = expander.get_macro(command_name) is None
    expander.skip_whitespace()
    block = expander.parse_brace_as_tokens()
    if is_definable and block:
        expander.push_tokens(block)
    return []


def make_ifloaded_handler(load_type: str = "package"):
    def ifloaded_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        expander.skip_whitespace()
        package_name = expander.parse_brace_name()
        blocks = expander.parse_braced_blocks(2)
        if len(blocks) != 2:
            expander.logger.warning(f"Warning: \\@if{load_type}loaded expects 3 blocks")
            return None

        if not package_name:
            return None
        package_name = package_name.strip()

        loaded_set = (
            expander.loaded_packages
            if load_type == "package"
            else expander.loaded_classes
        )
        block = blocks[0] if package_name in loaded_set else blocks[1]
        expander.push_tokens(block)
        return []

    return ifloaded_handler


def register_atifs(expander: ExpanderCore):

    if_handlers = {
        "\\@ifstar": if_star_handler,
        "\\@ifnextchar": if_nextchar_handler,
        "\\@ifmmode": if_mathmode_handler,
        "\\@ifundefined": if_undefined_handler,
        "\\@ifdefinable": ifdefinable_handler,
        "\\@ifpackageloaded": make_ifloaded_handler("package"),
        "\\@ifclassloaded": make_ifloaded_handler("class"),
    }
    for name, handler in if_handlers.items():
        macro = Macro(name, handler, MacroType.IF)
        expander.register_macro(name, macro, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_atifs(expander)

    text = r"""
    \makeatletter
    \def\cmd{\@ifnextchar[{OPT}{NO OPT}} 
    """.strip()

    expander.expand(text)
    out = expander.expand(r"\cmd [")  # OPT

    text = r"""
    \begin{equation}
    \@ifmmode{MATH}{NO MATH}
    """.strip()

    out2 = expander.expand(text)  # MATH

    out3 = expander.expand(r"\@ifundefined{cmddd}{UNDEFINED}{DEFINED}")  # UNDEFINED
