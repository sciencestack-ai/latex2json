from typing import List, Optional, Tuple
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.expander.handlers.registers.base_register_handlers import (
    NewRegisterMacro,
    RegisterMacro,
    registertype_macro_handler,
)
from latex2json.expander.macro_registry import Macro
from latex2json.registers.types import Box, RegisterType
from latex2json.tokens import Token
from latex2json.expander.expander_core import RELAX_TOKEN, ExpanderCore
from latex2json.tokens.types import TokenType

REGISTER_TYPE = RegisterType.BOX


def newbox_handler(expander: ExpanderCore, token: Token):
    # e.g. \newbox\mybox

    tok = expander.peek()
    if tok is None or tok.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(f"Warning: \\newbox expects a \\name, but found {tok}")
        return None
    box_name = tok.value
    expander.consume()

    expander.state.create_register(REGISTER_TYPE, box_name)
    # note that \mybox on its own is not a valid command in latex


def parse_box_id(expander: ExpanderCore) -> Optional[int | str]:
    reg_int_id = expander.parse_integer()
    if reg_int_id is not None:  # i.e. not \setbox0, check for \setbox\mybox...
        return reg_int_id

    expander.skip_whitespace()
    tok = expander.peek()
    if tok is None or tok.type != TokenType.CONTROL_SEQUENCE:
        return None

    if expander.get_register_value(REGISTER_TYPE, tok.value) is not None:
        expander.consume()
        return tok.value
    return None


def setbox_handler(expander: ExpanderCore, token: Token):
    # \setbox0=\vbox{123}, or \setbox\mybox=\vbox{123}
    box_id = parse_box_id(expander)
    if box_id is None:
        expander.logger.warning(
            f"Warning: \\setbox expects a valid box id, but found {expander.peek()}"
        )
        return None

    if not expander.parse_equals():
        expander.logger.warning(
            f"Warning: \\setbox expects a =, but found {expander.peek()}"
        )
        return None

    expander.skip_whitespace()
    box = expander.parse_box()
    if not box:
        expander.logger.warning(
            f"Warning: \\setbox expects a box, but found {expander.peek()}"
        )
        return None

    expander.set_register(REGISTER_TYPE, box_id, box)
    return []


def get_box_id_and_instance(expander: ExpanderCore, prefix: str = "\\box"):
    box_id = parse_box_id(expander)
    if box_id is None:
        expander.logger.warning(
            f"Warning: {prefix} expects a valid box id, but found {expander.peek()}"
        )
        return None

    box = expander.get_register_value(REGISTER_TYPE, box_id)
    if not isinstance(box, Box):
        expander.logger.warning(f"Warning: {prefix} expects a box, but found {box}")
        return None

    return box_id, box


def make_box_handler(copy=False):
    prefix = "\\copy" if copy else "\\box"

    def box_handler(expander: ExpanderCore, token: Token):
        out = get_box_id_and_instance(expander, prefix)
        if out is None:
            return None

        box_id, box = out

        out_tokens = box.content
        if not copy:
            # \box0 flushes the box
            box.content = []

        return out_tokens

    return box_handler


def make_boxdim_handler(dim: str):
    if dim not in ["wd", "ht", "dp"]:
        return None

    prefix = f"\\{dim}"

    def boxdim_handler(expander: ExpanderCore, token: Token):
        out = get_box_id_and_instance(expander, prefix)
        if out is None:
            return None

        box_id, box = out

        out_dim = 0
        if dim == "wd":
            out_dim = box.width
        elif dim == "ht":
            out_dim = box.height
        elif dim == "dp":
            out_dim = box.depth

        return expander.convert_str_to_tokens(str(out_dim))

    return boxdim_handler


def register_box_handlers(expander: ExpanderCore):
    expander.register_handler("newbox", newbox_handler, is_global=True)

    expander.register_handler(
        "setbox",
        setbox_handler,
        is_global=True,
    )

    expander.register_handler("box", make_box_handler(False), is_global=True)
    expander.register_handler("copy", make_box_handler(True), is_global=True)

    # width/height/depth
    for dim in ["wd", "ht", "dp"]:
        expander.register_handler(dim, make_boxdim_handler(dim), is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_box_handlers(expander)

    expander.expand(r"\newbox\mybox")
    expander.expand(r"\setbox0=\vbox{123}")
    out0 = expander.get_register_value(RegisterType.BOX, 0)

    expander.expand(r"\setbox\mybox=\hbox to 5pt{abc}")
    outmybox = expander.get_register_value(RegisterType.BOX, "mybox")
    # print(out0)
    # print(outmybox)

    boxcopy0 = expander.expand(r"\copy0")
    boxcopymybox = expander.expand(r"\copy\mybox")
    # print(boxcopy0)
    # print(boxcopymybox)
