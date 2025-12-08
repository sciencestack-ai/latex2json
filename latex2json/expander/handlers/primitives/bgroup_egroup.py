from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token, TokenType
from latex2json.tokens.utils import is_end_group_token


def bgroup_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.push_tokens([BEGIN_BRACE_TOKEN.copy()])
    return []


def egroup_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.push_tokens([END_BRACE_TOKEN.copy()])
    return []


def is_end_tokens(tok: Token) -> bool:
    return is_end_group_token(tok) or (
        tok.type == TokenType.CONTROL_SEQUENCE and tok.value == "end"
    )


def aftergroup_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    tok = expander.parse_immediate_token(skip_whitespace=True)
    if tok is None:
        return None
    tokens = expander.process(is_end_tokens, consume_stop_token=False)
    # push back the aftergroup tokens
    expander.push_tokens(tok)
    return tokens


# useful to define Macro as type=MacroType.CHAR so that it can be used in \ifx etc
def register_bgroup(expander: ExpanderCore):
    for bgroup in ["bgroup", "begingroup"]:
        expander.register_macro(
            bgroup,
            Macro(
                bgroup,
                bgroup_handler,
                definition=[BEGIN_BRACE_TOKEN.copy()],
                type=MacroType.CHAR,
            ),
            is_global=True,
        )
    for egroup in ["egroup", "endgroup"]:
        expander.register_macro(
            egroup,
            Macro(
                egroup,
                egroup_handler,
                definition=[END_BRACE_TOKEN.copy()],
                type=MacroType.CHAR,
            ),
            is_global=True,
        )

    # expander.register_handler("begingroup", begingroup_handler, is_global=True)
    # expander.register_handler("endgroup", endgroup_handler, is_global=True)

    expander.register_handler("aftergroup", aftergroup_handler, is_global=True)


if __name__ == "__main__":

    from latex2json.expander.expander import Expander

    expander = Expander()
