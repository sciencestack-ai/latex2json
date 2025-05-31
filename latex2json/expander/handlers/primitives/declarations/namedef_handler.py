from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import Token


def namedef_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    # Get both the name and definition blocks
    blocks = expander.parse_braced_blocks(2)
    if len(blocks) != 2:
        expander.logger.warning("\\@namedef: Requires name and definition arguments")
        return None

    name_tokens = blocks[0]
    definition = blocks[1]

    # Expand the name tokens to get the actual command name
    expanded_name = expander.expand_tokens(name_tokens)
    if not expanded_name:
        expander.logger.warning("\\@namedef: Failed to expand name")
        return None

    # Convert expanded tokens to string and ensure it starts with \
    name_str = "".join(token.value for token in expanded_name)

    # Create and register the macro
    def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        expander.push_tokens(definition)
        return []

    macro = Macro(name_str, handler, definition=definition)
    expander.register_macro(name_str, macro, is_global=True)

    return []


def register_namedef(expander: ExpanderCore):
    r"""Register the \@namedef command with the expander."""
    expander.register_macro(
        "\\@namedef",
        Macro("\\@namedef", namedef_handler),
        is_global=True,
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_namedef(expander)
    expander.expand(r"\makeatletter \@namedef{foo}{bar} \makeatother")
    out = expander.expand(r"\foo")
