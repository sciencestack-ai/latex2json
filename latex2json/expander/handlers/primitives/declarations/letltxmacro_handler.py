from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import Token, TokenType


def letltxmacro_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    cmd_name = expander.parse_command_name()
    expander.skip_whitespace()
    target_cmd_name = expander.parse_command_name()
    if not cmd_name:
        expander.logger.warning("\\letltxmacro: Requires a name argument")
        return None
    if not target_cmd_name:
        expander.logger.warning("\\letltxmacro: Requires a target name argument")
        return None

    target_macro = expander.get_macro(target_cmd_name)
    if target_macro is None:
        # push the control sequence as is
        def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
            target_cmd_token = Token(TokenType.CONTROL_SEQUENCE, target_cmd_name)
            return [target_cmd_token]

        expander.register_handler(
            cmd_name, handler, is_global=False, is_user_defined=True
        )

    else:
        macro = target_macro.copy()
        macro.name = cmd_name
        expander.register_macro(cmd_name, macro, is_global=False, is_user_defined=True)

    return []


def register_letltxmacro(expander: ExpanderCore):
    expander.register_macro(
        "\\LetLtxMacro",
        Macro("\\LetLtxMacro", letltxmacro_handler),
        is_global=True,
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    text = r"""
    \LetLtxMacro{\oldsqrt}{\sqrt}
    $\oldsqrt{2}$
"""
    expander = Expander()
    expander.expand(text)
    print(expander.convert_tokens_to_str(expander.expand(text)))
