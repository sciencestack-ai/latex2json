from typing import List, Optional
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token
from latex2json.expander.expander_core import ExpanderCore


def if_file_exists_handler(
    expander: ExpanderCore, token: Token
) -> Optional[List[Token]]:
    expander.skip_whitespace()
    file_name = expander.parse_brace_name()
    blocks = expander.parse_braced_blocks(2)
    if len(blocks) != 2:
        expander.logger.warning(f"\\IfFileExists expects 3 blocks")
        return None

    if not file_name:
        return None
    file_name = file_name.strip()

    block = blocks[0] if expander.if_file_exists(file_name) else blocks[1]
    expander.push_tokens(block)

    return []


def register_iffileexists(expander: ExpanderCore):
    if_file_exists_macro = Macro(
        "IfFileExists", handler=if_file_exists_handler, type=MacroType.IF
    )
    expander.register_macro("\\IfFileExists", if_file_exists_macro, is_global=True)
