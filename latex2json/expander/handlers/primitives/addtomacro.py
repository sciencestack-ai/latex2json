from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token


def addtomacro_handler(expander: ExpanderCore, token: Token):
    r"""
    \g@addto@macro{<macro>}{...}

    Adds ... to the definition of <macro>.
    """
    expander.skip_whitespace()
    cmd_token = expander.parse_command_name_token()
    expander.skip_whitespace()
    brace = expander.parse_brace_as_tokens()
    if not cmd_token:
        expander.logger.warning("\\g@addto@macro: Requires a macro argument")
        return None
    if brace is None:
        expander.logger.warning(
            "\\g@addto@macro: Requires a brace argument after macro"
        )
        return None
    # expander.push_tokens(brace)
    macro = expander.get_macro(cmd_token)

    if not macro:
        # just define it
        def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
            expander.push_tokens(brace.copy())
            return []

        macro = Macro(cmd_token, handler, definition=brace)
        expander.register_macro(
            cmd_token,
            macro,
            is_global=True,
            is_user_defined=True,
        )
    else:
        macro.definition.extend(brace)

    return []


def register_addtomacro_handler(expander: ExpanderCore):
    for cmd in ["g@addto@macro", "addto"]:
        expander.register_handler(cmd, addtomacro_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    text = r"""
    \makeatletter

    \def\foo{foo}
    \addto{\foo}{bar}

    \foo
    haha
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
