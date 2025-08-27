from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.expander.handlers.primitives.declarations.newcommand import (
    newcommand_handler,
)
from latex2json.expander.macro_registry import Macro
from latex2json.registers.defaults.boxes import ADVANCED_BOX_SPECS
from latex2json.tokens.types import (
    BEGIN_BRACKET_TOKEN,
    END_BRACKET_TOKEN,
    Token,
    TokenType,
)

ADVANCED_BOX_SPECS["tcbox"] = "[{"  # \tcbox[options]{text}


def newtcbox_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    options = expander.parse_bracket_as_tokens()

    out = newcommand_handler(expander, token)
    if out is None:
        return None

    cmd_name = out.cmd_token

    # print(out)

    def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        # Parse exactly num_args arguments
        args = expander.get_parsed_args(
            out.num_args, out.default_arg, command_name=cmd_name
        )
        if args is None:
            return None

        subbed = expander.substitute_token_args(out.definition, args)
        tokens = [Token(TokenType.CONTROL_SEQUENCE, "tcbox")]
        tokens += [BEGIN_BRACKET_TOKEN.copy()]
        tokens += subbed
        tokens += [END_BRACKET_TOKEN.copy()]
        return tokens

    expander.register_handler(cmd_name, handler, is_global=True, is_user_defined=True)

    return []


def register_tcolorbox(expander: ExpanderCore):
    expander.register_handler("newtcbox", newtcbox_handler, is_global=True)
    expander.register_handler("renewtcbox", newtcbox_handler, is_global=True)

    ignore_cmds = {
        # tcb
        "tcbset": "{",
        "tcbuselibrary": "{",
    }
    register_ignore_handlers_util(expander, ignore_cmds, expand=False)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    text = r"""
\newtcbox{\mymath}[1][default]{%
    nobeforeafter, math upper, tcbox raise base,
    enhanced, colframe=blue!30!black,
    colback=green!30, boxrule=1pt,
    #1}

    \mymath{BOX}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
