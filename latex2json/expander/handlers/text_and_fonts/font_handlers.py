from typing import List
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.types import Token, TokenType


def font_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()

    font_id = None
    cmd = expander.parse_command_name_token()
    if not cmd:
        font_id = expander.parse_integer()
        if font_id is None:
            expander.logger.info("\\font expects a font id, found %s", expander.peek())
            # consume the token
            # expander.parse_immediate_token()
            return None
    else:
        font_id = cmd.value

    if not expander.parse_equals():
        expander.logger.warning("\\font expects a = after the command name")
        return None

    expander.skip_whitespace()

    font_definition = expander.expand_until_eol_or_relax()

    expander.create_new_font(f"{font_id}", font_definition)

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
        expander.logger.warning("\\newfont expects a command name")
        return None

    expander.create_new_font(cmd.value, font_definition)

    return []


def font_dimen_handler(expander: ExpanderCore, token: Token):
    r"""
    \fontdimen2\font=\@IEEEtrantmpdimenA
    """
    expander.skip_whitespace()
    # only 1 integer. Dont use parse_integer since it will try to expand the next control sequence
    number = expander.consume()
    expander.skip_whitespace()
    cmd = expander.parse_command_name_token()

    if expander.parse_equals():
        expander.parse_dimensions(parse_unknown=True)

    return []


def resetfont_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    cmd = expander.parse_immediate_token()
    # simply ignore?
    return []


def register_font_handlers(expander: ExpanderCore):
    expander.register_handler(r"\font", font_handler, is_global=True)
    expander.register_handler(r"\newfont", newfont_handler, is_global=True)
    expander.register_handler(r"\fontdimen", font_dimen_handler, is_global=True)
    expander.register_handler(r"\reset@font", resetfont_handler, is_global=True)

    ignore_patterns = {
        "fontseries": "{",
        "normalem": 0,  # ignore since we dont currently distinguish em
        "newfam": "\\",  # e.g. \newfam\fontfam
        "url@samestyle": 0,  # used for url fonts
        "fontfamily": "{",
        "textfont": "\\=\\",  # e.g. \textfont\fontfam=\xxxx
        "scriptfont": "\\=\\",
        "scriptscriptfont": "\\=\\",
        "setmathfont": "[{",
        "theoremheaderfont": "{",
        # Font-related formatting
        "setmathfont": "[{",
        "theorembodyfont": "{",
        "setmainfont": 1,
        "setsansfont": 1,
        "setmonofont": 1,
        "fontsize": 2,
        "@setfontsize": 3,
        "selectfont": 0,
        "usefont": 4,
        "fontseries": 1,
        "fontshape": 1,
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
