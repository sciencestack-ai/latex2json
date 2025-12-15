from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.expander.handlers.sectioning.section_handlers import (
    make_section_handler,
)
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import wrap_tokens_in_braces


def caption_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    """Handle caption tokens."""
    float_env = expander.get_parent_float_env()
    cur_env = float_env.name if float_env else None

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


def captionbox_subcaptionbox_handler(
    expander: ExpanderCore, token: Token, is_subcaption: bool = False
) -> Optional[List[Token]]:
    r"""Handle captionbox/subcaptionbox tokens.
    Syntax: \[sub]captionbox[<list entry>]{<heading>}[<width>][<inner-pos>]{<contents>}

    transforms to \begin{subfigure} \caption{heading} contents \end{subfigure}
    """
    expander.skip_whitespace()

    # Check if starred version
    is_starred = expander.parse_asterisk()

    # Parse optional [list entry] (skip for starred version)
    if not is_starred:
        expander.parse_bracket_as_tokens()
    expander.skip_whitespace()

    # Parse required {heading} - this is the caption
    heading = expander.parse_brace_as_tokens() or []
    expander.skip_whitespace()

    # Parse optional [width] and [inner-pos] (ignore them)
    expander.parse_bracket_as_tokens()
    expander.skip_whitespace()
    expander.parse_bracket_as_tokens()
    expander.skip_whitespace()

    # Parse required {contents}
    contents = expander.parse_brace_as_tokens() or []

    # Determine if we should use subfigure or subtable
    float_env = expander.get_parent_float_env()
    is_table = float_env and float_env.name == "table"
    env_name = "table" if is_table else "figure"
    if is_subcaption:
        env_name = "sub" + env_name

    # Create tokens: \begin{subfigure} \caption{heading} contents \end{subfigure}
    env_name_tokens = expander.convert_str_to_tokens(env_name)
    env_name_tokens = wrap_tokens_in_braces(env_name_tokens)

    out_tokens = [
        Token(TokenType.CONTROL_SEQUENCE, "begin"),
        *env_name_tokens.copy(),
        Token(
            TokenType.CONTROL_SEQUENCE, "caption" if not is_subcaption else "subcaption"
        ),
        *wrap_tokens_in_braces(heading),
        *contents,
        Token(TokenType.CONTROL_SEQUENCE, "end"),
        *env_name_tokens.copy(),
    ]

    expander.push_tokens(out_tokens)
    return []


def register_caption_handler(expander: ExpanderCore):
    """Register caption handlers."""
    for caption in ["caption", "subcaption"]:
        expander.register_handler(caption, caption_handler, is_global=True)

    expander.register_handler("captionof", captionof_handler, is_global=True)

    # captionbox and subcaptionbox use the same handler with different parameters
    expander.register_handler(
        "captionbox",
        lambda exp, tok: captionbox_subcaptionbox_handler(
            exp, tok, is_subcaption=False
        ),
        is_global=True,
    )
    expander.register_handler(
        "subcaptionbox",
        lambda exp, tok: captionbox_subcaptionbox_handler(exp, tok, is_subcaption=True),
        is_global=True,
    )

    ignore_patterns = {
        "captionsetup": "[{",
        "DeclareCaptionFont": "{{",  # fontsize and line height
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
                print("CUR ENV", expander.current_env)
