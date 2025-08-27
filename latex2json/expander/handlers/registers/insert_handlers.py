from typing import List, Optional, Tuple
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.registers.types import RegisterType
from latex2json.tokens import Token
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import TokenType
from latex2json.tokens.utils import wrap_tokens_in_braces


def insert_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    cmd = expander.parse_command_name_token()
    if not cmd:
        expander.logger.warning(
            f"Warning: \\insert expects a name, but found {expander.peek()}"
        )
        return None

    expander.skip_whitespace()
    tokens = expander.parse_brace_as_tokens()
    if not tokens:
        return []

    # check if cmd is footins
    if cmd.value == "footins":
        # insert as simple footnote?
        footnote_tokens = [
            Token(TokenType.CONTROL_SEQUENCE, "footnote"),
            *wrap_tokens_in_braces(tokens),
        ]
        expander.push_tokens(footnote_tokens)

    return []


def register_insert_handlers(expander: ExpanderCore):
    # for builtin_insert in BUILTIN_INSERTS:
    #     expander.create_new_insert(builtin_insert)

    # expander.register_handler(
    #     "newinsert",
    #     newinsert_handler,
    #     is_global=True,
    # )

    expander.register_handler("insert", insert_handler, is_global=True)

    # parse and ignore these commands since we don't care about the actual latex dimensions for rendering
    ignore_patterns = {
        "reserveinserts": 1,
    }

    register_ignore_handlers_util(expander, ignore_patterns)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_insert_handlers(expander)

    text = r"""
    \makeatletter
    \newinsert\myins
    \insert\myins{ssss} 

    \skip\@mpfootins = \skip\footins
    \insert\footins{sss}
    \the\footins
"""
    #     text = r"""
    #     \skip\leftskip = \skip\rightskip
    # """
    text = r"""
    \newinsert\myins

"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    # print(out_str)

    print(expander.get_register_value(RegisterType.INSERT, "myins"))
