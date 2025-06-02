from typing import List, Optional, Tuple, Union
from latex2json.registers.types import Box, RegisterType
from latex2json.tokens import Token
from latex2json.expander.expander_core import RELAX_TOKEN, ExpanderCore
from latex2json.tokens.types import TokenType
from latex2json.expander.handlers.registers.base_register_handlers import RegisterMacro

REGISTER_TYPE = RegisterType.BOX
BOX_DIMENSIONS = ["wd", "ht", "dp"]


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


class BoxDimRegisterMacro(RegisterMacro):
    r"""Handles box dimension commands like \wd, \ht, \dp"""

    def __init__(self, dim: str, command_name: str):
        if dim not in BOX_DIMENSIONS:
            raise ValueError(f"Invalid box dimension: {dim}")

        super().__init__(
            RegisterType.DIMEN,
            command_name,
            self.handle_boxdim,  # Use method as handler
            is_id_integer=True,
        )
        self.dim = dim

    def _parse_register(
        self, expander: ExpanderCore, token: Token
    ) -> Tuple[RegisterType, Optional[Union[int, str]]]:
        if expander.peek() == token:
            expander.consume()

        box_id = parse_box_id(expander)
        if box_id is None:
            expander.logger.warning(
                f"Warning: \\{self.dim} expects a valid box id, but found {expander.peek()}"
            )
            return self.register_type, None

        reg_name = f"{self.dim}{box_id}"
        return self.register_type, reg_name

    def handle_boxdim(
        self, expander: ExpanderCore, token: Token
    ) -> Optional[List[Token]]:
        r"""Handle box dimension commands like \wd0=5pt"""
        register_type, reg_id = self._parse_register(expander, token)
        if reg_id is None:
            return None

        # check for = assignment
        if not expander.parse_equals():
            return expander.get_register_value_as_tokens(register_type, reg_id)

        # assignment phase
        expander.skip_whitespace()
        dim_val = expander.parse_dimensions()
        if dim_val is None:
            expander.logger.warning(
                f"Warning: \\{self.dim} expects = dimension, but found {expander.peek()}"
            )
            return None

        expander.set_register(register_type, reg_id, dim_val)
        return []


def make_box_handler(copy=False):
    r"""Handle \box and \copy commands"""
    prefix = "\\copy" if copy else "\\box"

    def box_handler(expander: ExpanderCore, token: Token):
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

        out_tokens = box.content
        if not copy:
            # \box0 flushes the box
            box.content = []

        return out_tokens

    return box_handler


def setbox_handler(expander: ExpanderCore, token: Token):
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


def newbox_handler(expander: ExpanderCore, token: Token):
    tok = expander.peek()
    if tok is None or tok.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(f"Warning: \\newbox expects a \\name, but found {tok}")
        return None
    box_name = tok.value
    expander.consume()

    expander.state.create_register(REGISTER_TYPE, box_name)
    return []


def register_box_handlers(expander: ExpanderCore):
    """Register all box-related handlers"""
    expander.register_handler("newbox", newbox_handler, is_global=True)
    expander.register_handler("setbox", setbox_handler, is_global=True)
    expander.register_handler("box", make_box_handler(False), is_global=True)
    expander.register_handler("copy", make_box_handler(True), is_global=True)

    # Register box dimension handlers (\wd, \ht, \dp)
    for dim in BOX_DIMENSIONS:
        expander.register_macro(
            dim,
            BoxDimRegisterMacro(dim, dim),
            is_global=True,
        )


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
