from typing import Callable, List, Optional, Tuple
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token, TokenType


def _parse_cmd_name_and_int_value(
    expander: ExpanderCore,
) -> Optional[Tuple[Token, int]]:
    expander.skip_whitespace()
    cmd = expander.parse_command_name_token()
    if not cmd:
        expander.logger.warning("\\chardef expects a command name")
        return None

    expander.parse_equals()
    expander.skip_whitespace()
    value = expander.parse_integer()
    if value is None:
        return None

    return cmd, value


def _parse_and_assign_def_values(
    expander: ExpanderCore, value_check_fn: Callable[[int], bool]
):
    out = _parse_cmd_name_and_int_value(expander)
    if not out:
        return False, None, None

    cmd, value = out

    if not value_check_fn(value):
        return False, cmd, value

    catcode = expander.get_catcode(value)
    char = chr(value)
    out_token = Token(TokenType.CHARACTER, value=char, catcode=catcode)
    handler = lambda expander, token: [out_token]
    macro = Macro(cmd, handler, [out_token], type=MacroType.CHAR)
    expander.register_macro(cmd, macro, is_global=False, is_user_defined=True)

    return True, cmd, value


def chardef_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    rt, cmd, value = _parse_and_assign_def_values(
        expander, lambda value: 0 <= value <= 255
    )

    if not rt:
        if cmd:
            expander.logger.warning(
                f"\\chardef {cmd} = {value} out of valid range (0-255)"
            )
        else:
            expander.logger.warning(
                "\\chardef expects a valid command name + value str"
            )
        return None

    return []


def mathchardef_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    rt, cmd, value = _parse_and_assign_def_values(
        expander, lambda value: 0 <= value <= 32767
    )

    if not rt:
        if cmd:
            expander.logger.warning(
                f"\\mathchardef {cmd} = {value} out of valid range (0-32767)"
            )
        else:
            expander.logger.warning(
                "\\mathchardef expects a valid command name + value str"
            )
        return None

    return []


def register_chardef_handlers(expander: ExpanderCore):
    expander.register_handler("\\chardef", chardef_handler, is_global=True)
    expander.register_handler("\\mathchardef", mathchardef_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    text = r"""
    \chardef\test='101
    \test
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
