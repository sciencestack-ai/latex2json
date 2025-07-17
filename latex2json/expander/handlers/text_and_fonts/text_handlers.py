from latex2json.expander.state import ProcessingMode
from latex2json.latex_maps.fonts import (
    TEXT_MODE_COMMANDS,
)
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token
from latex2json.tokens.utils import wrap_tokens_in_braces


def text_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    # force text mode
    expander.state.push_mode(ProcessingMode.TEXT)
    text_tokens = expander.parse_immediate_token(expand=True)
    out_tokens = None
    if text_tokens:
        out_tokens = [token] + wrap_tokens_in_braces(text_tokens)
    expander.state.pop_mode()
    return out_tokens


def textcolor_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    color = expander.parse_brace_name()
    if not color:
        expander.logger.warning("Warning: \\textcolor expects a color {...}")
        return None
    expander.skip_whitespace()

    # force text mode
    expander.state.push_mode(ProcessingMode.TEXT)
    out_tokens = None
    text_tokens = expander.parse_immediate_token(expand=True)
    if text_tokens:
        color_brace_tokens = expander.convert_str_to_tokens("{" + color + "}")
        out_tokens = [token] + color_brace_tokens + wrap_tokens_in_braces(text_tokens)
    expander.state.pop_mode()
    return out_tokens


def register_text_handlers(expander: ExpanderCore):
    r"""
    The reason we create text handler here is to:
    1) convert non-braced arguments to braced arguments e.g. \textbf abc to \textbf{a}bc
    2) force text mode switch for \text...{} commands

    We return the raw \text...{...} tokens for parser to handle in later stages
    """
    expander.register_handler("text", text_handler, is_global=True)
    for cmd in TEXT_MODE_COMMANDS:
        expander.register_handler(cmd, text_handler, is_global=True)

    expander.register_handler("textcolor", textcolor_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander
    from latex2json.tokens.types import Token

    expander = Expander()
    out = expander.expand(r"$_\textbf{Hello _ $1+1$ after }_$")
    print(out)
