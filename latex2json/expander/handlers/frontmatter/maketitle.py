from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import Handler
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import (
    WHITESPACE_TOKEN,
    Token,
    TokenType,
    CommandWithArgsToken,
)
from latex2json.tokens.utils import (
    is_begin_group_token,
    strip_whitespace_tokens,
    wrap_tokens_in_braces,
)


def make_frontmatter_key_handler(key: str) -> Handler:
    r"""
    Handler for \title, \author, etc.
    These are storage-only commands - they update state.frontmatter but emit nothing.
    This allows users to redefine them if needed while preserving storage.
    """

    at_key = "@" + key

    def handler(expander: ExpanderCore, token: Token) -> List[Token]:
        expander.skip_whitespace()
        bracket = expander.parse_bracket_as_tokens()  # Optional short title
        expander.skip_whitespace()
        tokens = expander.parse_immediate_token(expand=False) or []

        if key == "author":
            # append
            existing_author_tokens = expander.state.frontmatter.get(key, [])
            if existing_author_tokens and tokens:
                existing_author_tokens.extend(
                    [
                        WHITESPACE_TOKEN.copy(),
                        Token(TokenType.CONTROL_SEQUENCE, "and"),
                        WHITESPACE_TOKEN.copy(),
                    ]
                )
            tokens = existing_author_tokens + tokens

        expander.state.frontmatter[key] = tokens

        # Emit nothing - metadata is stored, not rendered yet
        return []

    return handler


def make_at_frontmatter_key_handler(key: str) -> Handler:
    r"""
    Handler for \@title, \@author, etc.
    These are the SOURCE OF TRUTH - they always emit from state.frontmatter.
    Even if user redefines these with \def, we intercept to preserve semantic info.
    Returns CommandWithArgsToken for semantic preservation through the pipeline.
    """

    def handler(expander: ExpanderCore, token: Token) -> List[Token]:
        # Always read from state.frontmatter
        tokens = expander.state.frontmatter.get(key, [])
        if not tokens:
            return []

        # expander.push_tokens(tokens)
        # return []

        # Expand stored tokens to resolve any macros
        expanded = expander.expand_tokens(tokens)

        # Return semantic CommandWithArgsToken
        # This preserves the semantic meaning even inside redefined \@maketitle
        cmd_token = CommandWithArgsToken(
            name=key,
            args=[expanded],
        )
        return [cmd_token]

    return handler


def at_maketitle_handler(expander: ExpanderCore, token: Token) -> List[Token]:
    r"""
    Default \@maketitle implementation.
    Emits all frontmatter by calling \@title, \@author, etc.
    Returns a single CommandWithArgsToken wrapping all frontmatter for isolated processing.
    Users can redefine this with \renewcommand{\@maketitle}{...}
    """
    out_tokens: List[Token] = []

    # Collect all frontmatter CommandWithArgsTokens
    for key in expander.state.frontmatter:
        exp = expander.expand_tokens([Token(TokenType.CONTROL_SEQUENCE, "@" + key)])
        if exp:
            out_tokens.extend(exp)

    # Wrap everything in a maketitle CommandWithArgsToken for isolated processing
    return [CommandWithArgsToken("maketitle", args=[out_tokens])]


def maketitle_handler(expander: ExpanderCore, token: Token) -> List[Token]:
    r"""
    Handler for \maketitle.
    Delegates to \@maketitle (which user may have redefined).
    """
    # Push \@maketitle to stream - allows user redefinitions to work
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "@maketitle")])
    return []


def register_maketitle_handlers(expander: ExpanderCore):
    r"""
    Register handlers for frontmatter/metadata system.

    Design:
    - \title, \author, etc. are storage-only (can be redefined by users)
    - \@title, \@author, etc. are protected accessors (always read from state.frontmatter)
    - \maketitle delegates to \@maketitle
    - \@maketitle calls \@title, \@author, etc. to emit semantic tokens
    """
    # Register \maketitle and \@maketitle
    expander.register_handler("maketitle", maketitle_handler, is_global=True)
    expander.register_handler("@maketitle", at_maketitle_handler, is_global=True)

    frontmatter_keys = expander.state.frontmatter.keys()

    # Register user-visible metadata collectors: \title, \author, etc.
    for key in frontmatter_keys:
        expander.register_handler(
            key, make_frontmatter_key_handler(key), is_global=True
        )
        expander.register_handler(
            "@" + key, make_at_frontmatter_key_handler(key), is_global=True
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander
    from latex2json.tokens.types import Token

    expander = Expander()

    text = r"""
    \makeatletter
\def\@maketitle{
    \begin{tabular}[t]{c}\@author
    \end{tabular}
}
\def\maketitle{
    \@maketitle
}

\title{Caffe: Convolutional Architecture}

\def\alignauthor{
    \end{tabular}
  \begin{tabular}[t]{c}
}

\author{
    \alignauthor Yangqing Jia$^*$ \\
}

\maketitle

\begin{abstract}
Caffe Abstract
\end{abstract}
"""

    tokens = expander.expand(text)
    strip_whitespace_tokens(tokens)
    # out_str = expander.convert_tokens_to_str(tokens).strip()
    # print(out_str)
