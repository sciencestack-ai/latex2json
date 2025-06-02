from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.if_else.base_if import IfMacro
from latex2json.registers.types import RegisterType
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens


def newbool_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    bool_name = expander.parse_brace_name()
    if not bool_name:
        expander.logger.warning(
            f"Warning: \\newbool expects a boolean name, but found {expander.peek()}"
        )
        return None

    expander.state.create_register(RegisterType.BOOL, bool_name, False)

    return None


def make_setbool_handler(flag: bool):
    def setbool_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        expander.skip_whitespace()
        bool_name = expander.parse_brace_name()
        if not bool_name:
            expander.logger.warning(
                f"Warning: \\booltrue/false expects a boolean name, but found {expander.peek()}"
            )
            return None

        expander.state.set_register(RegisterType.BOOL, bool_name, flag)
        return None

    return setbool_handler


def if_bool_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    blocks = expander.parse_braced_blocks(3)

    if len(blocks) != 3:
        expander.logger.warning("Warning: \\ifbool expects 3 blocks")
        return None

    eval_block = blocks[0]
    bool_name = expander.convert_tokens_to_str(eval_block)
    bool_value = expander.state.get_register(RegisterType.BOOL, bool_name)
    # if not bool_value:
    #     expander.logger.warning(f"Warning: \\ifbool expects a boolean name")
    #     return None

    block = blocks[1] if bool_value else blocks[2]
    expander.push_tokens(block)
    return []


def set_boolean_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    bool_name = expander.parse_brace_name()
    if not bool_name:
        expander.logger.warning(
            f"Warning: \\setboolean expects a boolean name, but found {expander.peek()}"
        )
        return None

    expander.skip_whitespace()
    value = expander.parse_brace_name().strip()
    if not value:
        expander.logger.warning(
            f"Warning: \\setboolean expects a boolean value, but found {expander.peek()}"
        )
        return None

    flag = value.lower() == "true"

    expander.state.set_register(RegisterType.BOOL, bool_name, flag)
    return []


def register_bool_handlers(expander: ExpanderCore):
    r"""
    \newboolean{myflag}           % Create boolean
    \setboolean{myflag}{true}     % Set to true
    \setboolean{myflag}{false}    % Set to false
    % meant for \ifthenelse{\boolean{myflag}}{true code}{false code} but ifthenelse handled separately

    \newbool{myflag}              % Create boolean
    \booltrue{myflag}             % Set to true
    \boolfalse{myflag}            % Set to false
    \ifbool{myflag}{true code}{false code}
    """

    for newbool in ["newbool", "newboolean"]:
        expander.register_handler(
            newbool,
            newbool_handler,
            is_global=True,
        )

    expander.register_handler(
        "setboolean",
        set_boolean_handler,
        is_global=True,
    )

    expander.register_handler(
        "booltrue",
        make_setbool_handler(True),
        is_global=True,
    )

    expander.register_handler(
        "boolfalse",
        make_setbool_handler(False),
        is_global=True,
    )

    # ifbool
    expander.register_handler("ifbool", if_bool_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_bool_handlers(expander)
    # test in scope
    text = r"""
    \newbool{mybool}
    \booltrue{mybool}
    \ifbool{mybool}{True}{False}
    """.strip()
    out = expander.expand(text)
    print(out)
