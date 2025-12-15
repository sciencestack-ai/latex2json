from typing import List
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import convert_str_to_tokens, wrap_tokens_in_braces
from latex2json.utils.tex_utils import parse_key_val_string


def _convert_path_to_includegraphics(path: str) -> List[Token]:
    path_tokens = convert_str_to_tokens(path, catcode=Catcode.LETTER)
    return [
        Token(TokenType.CONTROL_SEQUENCE, "includegraphics"),
        *wrap_tokens_in_braces(path_tokens),
    ]


def psfig_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    brace_str = expander.parse_brace_name()
    if not brace_str:
        expander.logger.warning(f"\\[e]psfig expects a path")
        return None

    opts = parse_key_val_string(brace_str)
    if not opts:
        return []
    keys = ["file", "figure"]
    for key in keys:
        if key in opts:
            path = opts[key]
            return _convert_path_to_includegraphics(path)
    return []


def epsfbox_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    path = expander.parse_brace_name()
    if not path:
        expander.logger.warning(f"\\epsfbox expects a path")
        return None

    return _convert_path_to_includegraphics(path)


def register_epsfig(expander: ExpanderCore):
    # convert these to includegraphics..
    for cmd in ["epsfig", "psfig"]:
        expander.register_handler(cmd, psfig_handler, is_global=True)
    expander.register_handler("epsfbox", epsfbox_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_epsfig(expander)

    text = r"""
    \epsfig{file=eee.eps,other=opts}
    \epsfbox{aaa.eps}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
