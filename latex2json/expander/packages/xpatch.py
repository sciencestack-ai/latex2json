from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import find_token_sequence


def xpatch_handler(expander: ExpanderCore, token: Token):
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "patchcmd")])
    return []


def xpretocmd_handler(expander: ExpanderCore, token: Token):
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "pretocmd")])
    return []


def xapptocmd_handler(expander: ExpanderCore, token: Token):
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "apptocmd")])
    return []


def register_xpatch_handler(expander: ExpanderCore):
    # uses etoolbox functions internally
    expander.register_handler("xpatchcmd", xpatch_handler, is_global=True)
    expander.register_handler("xpretocmd", xpretocmd_handler, is_global=True)
    expander.register_handler("xapptocmd", xapptocmd_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    text = r"""
    \makeatletter

    \def\foo{foo}
    \xpatchcmd{\foo}{o}{ MIDDLE O }{success}{failure}

    \foo

    \xpretocmd{\foo}{prepend }{success}{failure}
    \foo

    \xapptocmd{\foo}{ append}{success}{failure}
    \foo
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
