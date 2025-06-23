from typing import List, Optional, Tuple, Union
from latex2json.expander.handlers.handler_utils import make_generic_command_handler
from latex2json.expander.macro_registry import Handler, Macro
from latex2json.latex_maps.boxes import BOXES
from latex2json.registers.types import Box, RegisterType
from latex2json.tokens import Token
from latex2json.expander.expander_core import RELAX_TOKEN, ExpanderCore
from latex2json.tokens.types import CommandWithArgsToken, TokenType
from latex2json.expander.handlers.registers.base_register_handlers import (
    RegisterMacro,
    make_register_macro,
)
from latex2json.tokens.utils import strip_whitespace_tokens

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


def box_n_copy_handler(copy=False):
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

        out_tokens = box.content.copy()
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


def make_savebox_handler(extended=False):
    r"""
    % Simple storage
    \sbox{\mybox}{Hello World}

    % Extended storage with width specification
    \savebox{\mybox}[3cm][c]{Centered text in 3cm width}
    """

    def savebox_handler(expander: ExpanderCore, token: Token):
        box_name = expander.parse_command_name()
        if box_name is None:
            expander.logger.warning(
                f"Warning: \\sbox|savebox expects a name, but found {expander.peek()}"
            )
            return None

        if extended:
            # ignore blocks..
            blocks = expander.parse_braced_blocks(
                N_blocks=2,
                brackets=True,
            )

        expander.skip_whitespace()
        box_content = expander.parse_brace_as_tokens(expand=True)
        if box_content is None:
            expander.logger.warning(
                f"Warning: \\sbox|savebox expects box content, but found {expander.peek()}"
            )
            return None

        existing_box: Optional[Box] = expander.get_register_value(
            REGISTER_TYPE, box_name
        )
        if existing_box is None:
            box = Box(content=box_content)
        else:
            box = existing_box
            box.content = box_content

        expander.set_register(REGISTER_TYPE, box_name, box)

        return []

    return savebox_handler


def usebox_handler(expander: ExpanderCore, token: Token):
    box_name = expander.parse_command_name()
    if box_name is None:
        expander.logger.warning(
            f"Warning: \\usebox expects a name, but found {expander.peek()}"
        )
        return None

    box = expander.get_register_value(REGISTER_TYPE, box_name)
    if isinstance(box, Box):
        return box.content.copy()

    return []


def _create_box_register(expander: ExpanderCore, box_name: str):
    expander.state.create_register(REGISTER_TYPE, box_name)
    # create a macro for the register
    # return the token itself as is, since we need it for setbox/copy/usebox etc
    macro = Macro(
        box_name,
        lambda expander, token: [token],
    )
    expander.register_macro(
        box_name,
        macro,
        is_global=True,
        is_user_defined=True,
    )


def newbox_handler(expander: ExpanderCore, token: Token):
    tok = expander.peek()
    if tok is None or tok.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(f"Warning: \\newbox expects a \\name, but found {tok}")
        return None
    box_name = tok.value
    expander.consume()

    _create_box_register(expander, box_name)
    return []


def newsavebox_handler(expander: ExpanderCore, token: Token):
    box_name = expander.parse_command_name()
    if box_name is None:
        expander.logger.warning(
            f"Warning: \\newsavebox expects a name, but found {expander.peek()}"
        )
        return None

    _create_box_register(expander, box_name)
    return []


def direct_box_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    # push the current box token to the stack so that we can parse_box
    expander.push_tokens([token])
    box = expander.parse_box()
    if box is None:
        return None

    return box.content


def box_manipulation_handler(expander: ExpanderCore, token: Token):
    """parse dimensions and ignored"""
    expander.skip_whitespace()
    dims = expander.parse_dimensions()
    expander.skip_whitespace()

    return []


CONTENT_BOX_SPECS = {
    "fbox": "{",  # \fbox{text}
    "parbox": "[[[{{",  # \parbox[pos][height][inner-pos]{width}{text}
    "makebox": "[[{",  # \makebox[width]{text}
    "framebox": "[[{",  # \framebox[width][pos]{text}
    "raisebox": "{[[{",  # \raisebox{distance}[extend-above][extend-below]{text}
    "colorbox": "{{",  # \colorbox{color}{text}
    "fcolorbox": "{{{",  # \fcolorbox{border}{bg}{text}
    "scalebox": "{{",  # \scalebox{scale}{text}
    "mbox": "{",  # \mbox{text}, strip out all EOL
    "pbox": "{{",  # \pbox{x}{text}
    "resizebox": "{{{",  # \resizebox{width}{height}{text}
    "rotatebox": "{{",  # \rotatebox{angle}{text}
    "adjustbox": "{{",  # \adjustbox{max width=\textwidth}{text}
}


def make_content_box_handler(command: str, argspec: str) -> Handler:
    handler = make_generic_command_handler(command, argspec)

    def content_box_handler(
        expander: ExpanderCore, token: Token
    ) -> Optional[list[Token]]:
        tokens = handler(expander, token)
        if tokens and isinstance(tokens[0], CommandWithArgsToken):
            # the last arg is the text content itself
            last_arg = tokens[0].args[-1]
            if isinstance(last_arg, list):
                out_tokens = strip_whitespace_tokens(last_arg)
                if command == "mbox":
                    return [t for t in out_tokens if t.type != TokenType.END_OF_LINE]
                return out_tokens
        return []

    return content_box_handler


def register_box_handlers(expander: ExpanderCore):
    """Register all box-related handlers"""

    # newbox, newsavebox
    expander.register_handler("newbox", newbox_handler, is_global=True)
    expander.register_handler("newsavebox", newsavebox_handler, is_global=True)

    # setbox/savebox
    expander.register_handler("setbox", setbox_handler, is_global=True)
    expander.register_handler(
        "sbox", make_savebox_handler(extended=False), is_global=True
    )
    expander.register_handler(
        "savebox", make_savebox_handler(extended=True), is_global=True
    )

    # box usage: usebox
    expander.register_handler("usebox", usebox_handler, is_global=True)
    # treat them the same semantically
    for cmd in ["box", "unvbox", "unhbox", "copy"]:
        expander.register_handler(
            cmd, box_n_copy_handler(cmd.endswith("copy")), is_global=True
        )

    # box content
    for cmd, spec in CONTENT_BOX_SPECS.items():
        expander.register_handler(
            cmd, make_content_box_handler(cmd, spec), is_global=True
        )

    # hbox, vbox, vtop
    for cmd in BOXES:
        expander.register_handler(cmd, direct_box_handler, is_global=True)

    # box manipulation handlers (parse dimensions and ignored)
    for cmd in ["moveleft", "moveright", "raise", "lower"]:
        expander.register_handler(cmd, box_manipulation_handler, is_global=True)

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
