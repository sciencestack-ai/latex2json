from typing import List, Optional, Tuple
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.expander.handlers.registers.base_register_handlers import (
    make_register_macro,
)
from latex2json.expander.macro_registry import Macro
from latex2json.registers.types import RegisterType
from latex2json.tokens import Token
from latex2json.expander.expander_core import RELAX_TOKEN, ExpanderCore

REGISTER_TYPE = RegisterType.DIMEN


def make_length_setter_handler(command_name: str):
    def length_setter_handler(
        expander: ExpanderCore, token: Token
    ) -> Optional[List[Token]]:
        expander.skip_whitespace()
        cmd = expander.parse_command_name_token()
        if not cmd:
            # expander.logger.warning(f"\\{command_name} expects a length name")
            return None

        length_name = cmd.value

        expander.skip_whitespace()
        block = expander.parse_immediate_token()
        if not block:
            expander.logger.info(
                f"\\{command_name} {length_name} expects a length value"
            )
            return None

        # NOTE: Dont add complexity of additional parsing since our parser does not care about the actual length value

        # expander.push_tokens(block + [RELAX_TOKEN.copy()])
        # expander.skip_whitespace()
        # tok = expander.peek()
        # if tok == RELAX_TOKEN:
        #     expander.consume()

        # if parsed is None:
        #     expander.logger.info(
        #         f"\\{command_name} expects proper dimensions, found {expander.peek()}"
        #     )
        #     return None

        return [length_name, 0]

    return length_setter_handler


def setlength_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    result = make_length_setter_handler("setlength")(expander, token)
    if result is None:
        return None
    length_name, parsed = result
    expander.set_register(REGISTER_TYPE, length_name, parsed)
    return []


def addtolength_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    result = make_length_setter_handler("addtolength")(expander, token)
    if result is None:
        return None
    length_name, parsed = result

    reg_type: RegisterType | None = None
    for rt in [RegisterType.DIMEN, RegisterType.SKIP]:
        current_value = expander.get_register_value(rt, length_name)
        if current_value is not None:
            reg_type = rt
            break

    if reg_type is None:
        expander.logger.warning(f"Length {length_name} not defined")
        return None

    expander.set_register(reg_type, length_name, current_value + parsed)
    return []


def newlength_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    cmd = expander.parse_command_name_token()
    if not cmd:
        expander.logger.warning("\\newlength expects a length name")
        return None

    expander.state.create_register(REGISTER_TYPE, cmd.value)
    # create a macro for the register
    expander.register_macro(
        cmd,
        make_register_macro(REGISTER_TYPE, cmd.value, is_id_integer=False),
        is_global=True,
        is_user_defined=True,
    )


def register_length_handlers(expander: ExpanderCore):
    expander.register_handler(
        "newlength",
        newlength_handler,
        is_global=True,
    )

    expander.register_macro(
        "setlength",
        Macro("setlength", setlength_handler, []),
        is_global=True,
    )

    expander.register_macro(
        "addtolength",
        Macro("addtolength", addtolength_handler, []),
        is_global=True,
    )

    # parse and ignore these commands since we don't care about the actual latex dimensions for rendering
    setlength_ignore_patterns = {
        "settoheight": 2,
        "settowidth": 2,
        "settodepth": 2,
    }

    register_ignore_handlers_util(expander, setlength_ignore_patterns)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_length_handlers(expander)

    # expander.expand(r"\newlength{\mylength}")
    # out = expander.expand(r"\setlength{\mylength}{1em}")
    out = expander.expand(r"\addtolength{\parskip}{-1em}")

    # print(expander.get_register_value(REGISTER_TYPE, "mylength"))

    # out = expander.expand(r"\addtolength{\textheight}{1em}")
    # print(out)
    # print(expander.get_register_value(REGISTER_TYPE, "textheight"))

    # expander.expand(r"\textwidth=10pt")
    # print(expander.get_register_value(REGISTER_TYPE, "textwidth"))
