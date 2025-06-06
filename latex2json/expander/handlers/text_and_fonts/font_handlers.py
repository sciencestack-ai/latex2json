from typing import List
from latex2json.expander.expander_core import ExpanderCore, is_relax_token
from latex2json.tokens.types import Token, TokenType


def font_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    font_cmd_token = expander.consume()
    if not font_cmd_token or font_cmd_token.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning("Warning: \\font expects a font command name")
        return None

    cmd_name = font_cmd_token.value

    if not expander.parse_equals():
        expander.logger.warning("Warning: \\font expects a = after the command name")
        return None

    expander.skip_whitespace()

    font_definition: List[Token] = []
    while not expander.eof():
        tokens = expander.expand_next()
        if not tokens:
            break

        break_out = False
        for i, tok in enumerate(tokens):
            if is_relax_token(tok):
                expander.push_tokens(tokens[i + 1 :])
                break_out = True
                break
            elif tok.type == TokenType.END_OF_LINE:
                expander.push_tokens(tokens[i:])
                break_out = True
                break
            else:
                font_definition.append(tok)

        if break_out:
            break

    expander.create_new_font(cmd_name, font_definition)

    return []


def register_font_handlers(expander: ExpanderCore):
    expander.register_handler(r"\font", font_handler, is_global=True)


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
