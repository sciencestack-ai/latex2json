from typing import Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def make_formatting_ignore_handler(pattern: str, n_blocks: int):
    def ignore_handler(expander: ExpanderCore, token: Token) -> Optional[list[Token]]:
        blocks = expander.parse_braced_blocks(n_blocks)
        return []

    return ignore_handler


def register_ignore_handlers_util(
    expander: ExpanderCore, ignore_patterns: dict[str, int]
):
    """Register all formatting-related command handlers"""
    for command, n_blocks in ignore_patterns.items():
        expander.register_handler(
            command,
            make_formatting_ignore_handler(command, n_blocks),
            is_global=True,
        )
