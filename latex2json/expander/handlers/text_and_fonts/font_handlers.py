from typing import List
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.types import Token, TokenType


def font_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    cmd = expander.parse_command_name_token()
    if not cmd:
        expander.logger.warning("Warning: \\font expects a font command name")
        return None

    if not expander.parse_equals():
        expander.logger.warning("Warning: \\font expects a = after the command name")
        return None

    expander.skip_whitespace()

    font_definition = expander.expand_until_eol_or_relax()

    expander.create_new_font(cmd.value, font_definition)

    return []


def newfont_handler(expander: ExpanderCore, token: Token):
    r"""
    \newfont{\grecomath}{cmmi12 at 15pt}
    """
    expander.skip_whitespace()
    cmd = expander.parse_command_name_token()
    expander.skip_whitespace()
    font_definition = expander.parse_brace_as_tokens() or []
    if not cmd:
        expander.logger.warning("Warning: \\newfont expects a command name")
        return None

    expander.create_new_font(cmd.value, font_definition)

    return []


def register_font_handlers(expander: ExpanderCore):
    expander.register_handler(r"\font", font_handler, is_global=True)
    expander.register_handler(r"\newfont", newfont_handler, is_global=True)

    ignore_patterns = {
        "newfam": "\\",  # e.g. \newfam\fontfam
        "fontfamily": "{",
        "textfont": "\\=\\",  # e.g. \textfont\fontfam=\xxxx
        "scriptfont": "\\=\\",
        "scriptscriptfont": "\\=\\",
        "setmathfont": "[{",
        "theoremheaderfont": "{",
    }
    register_ignore_handlers_util(expander, ignore_patterns)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_font_handlers(expander)

    text = r"""
\def\bigfont{BIG FONT}
\font\bigfont=cmr10 at asdsd
\bigfont
"""
    out = expander.expand(text)
