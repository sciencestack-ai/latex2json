from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.expander.handlers.sectioning.section_handlers import (
    make_section_handler,
)
from latex2json.tokens.types import Token, TokenType


def caption_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    """Handle caption tokens."""
    cur_env = expander.state.current_env

    return make_section_handler("caption", counter_name=cur_env)(expander, token)


def captionof_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    """Handle captionof tokens."""
    env_name = expander.parse_brace_name()
    if not env_name:
        expander.logger.warning("captionof: missing environment name")
        return None

    out = make_section_handler("caption", counter_name=env_name)(expander, token)
    if not out:
        return None
    caption_token = out[0]
    # make opt arg the env name + numbering i.e. equivalent to \caption[Figure 1]{CAPTION}
    caption_token.opt_args = [
        expander.convert_str_to_tokens(
            env_name.capitalize() + " " + (caption_token.numbering or "")
        )
    ]
    return out


def register_caption_handler(expander: ExpanderCore):
    """Register caption handlers."""
    for caption in ["caption", "subcaption"]:
        expander.register_handler(caption, caption_handler, is_global=True)

    expander.register_handler("captionof", captionof_handler, is_global=True)

    ignore_patterns = {
        "captionsetup": "[{",
    }
    register_ignore_handlers_util(expander, ignore_patterns)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander
    from latex2json.tokens.utils import strip_whitespace_tokens

    expander = Expander()
    register_caption_handler(expander)

    text = r"""
    \counterwithin{figure}{section}

    \section{SECTION}
    \begin{figure}[htb]
        \caption{FIGURE}
        \begin{subfigure}{sss}
            \caption{SUBFIGURE 2}
        \end{subfigure}
    \end{figure}

    \begin{table}[htb]
    \caption[SHORT]{TABLE}
    \end{table}

    \section{SECTION 2}
    \begin{figure}[htb] % reset counter
        \caption{FIGURE 2}
    \end{figure}
    """
    expander.set_text(text)
    while not expander.eof():
        tokens = expander.next_non_expandable_tokens()
        out = strip_whitespace_tokens(tokens)
        if out:
            if out[0].value == "caption":
                print(out)
                print("CUR ENV", expander.state.current_env)
