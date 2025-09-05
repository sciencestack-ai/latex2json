from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import Handler
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import wrap_tokens_in_braces


def get_frontmatter_key_to_tokens(
    expander: ExpanderCore, key: str
) -> Optional[List[Token]]:
    if key not in expander.state.frontmatter:
        return None
    tokens = expander.state.frontmatter[key]
    if not tokens:
        return None

    out_tokens: List[Token] = []
    tokens_exp = expander.expand_tokens(tokens)
    # e.g. output \author{...} for parser later to handle
    out_tokens.append(Token(TokenType.CONTROL_SEQUENCE, key))
    out_tokens.extend(wrap_tokens_in_braces(tokens_exp))
    return out_tokens


def at_maketitle_handler(expander: ExpanderCore, token: Token) -> List[Token]:
    # return all frontmatter tokens?
    out_tokens: List[Token] = []
    for key in expander.state.frontmatter.keys():
        tokens = get_frontmatter_key_to_tokens(expander, key)
        if tokens:
            out_tokens.extend(tokens)
    return out_tokens


def maketitle_handler(expander: ExpanderCore, token: Token) -> List[Token]:
    expander.push_tokens([Token(TokenType.CONTROL_SEQUENCE, "@maketitle")])
    return []


def make_frontmatter_key_handler(key: str) -> Handler:
    def handler(expander: ExpanderCore, token: Token) -> List[Token]:
        tokens = expander.parse_immediate_token(expand=False, skip_whitespace=True)
        if key not in expander.state.frontmatter:
            expander.state.frontmatter[key] = []
        if key == "author":
            # additive
            expander.state.frontmatter[key].extend(tokens)
        else:
            expander.state.frontmatter[key] = tokens
        return []

    return handler


def make_at_frontmatter_key_handler(key: str) -> Handler:
    def handler(expander: ExpanderCore, token: Token) -> List[Token]:
        return get_frontmatter_key_to_tokens(expander, key)

    return handler


def register_maketitle_handlers(expander: ExpanderCore):
    # maketitle
    expander.register_handler("maketitle", maketitle_handler, is_global=True)
    expander.register_handler("@maketitle", at_maketitle_handler, is_global=True)

    # frontmatter/metadata keys
    for cmd in ["author", "title", "date"]:
        expander.register_handler(
            cmd, make_frontmatter_key_handler(cmd), is_global=True
        )
        expander.register_handler(
            f"@{cmd}", make_at_frontmatter_key_handler(cmd), is_global=True
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander
    from latex2json.tokens.types import Token

    expander = Expander()

    register_maketitle_handlers(expander)

    text = r"""
    \author{Yu Deng \xxx}
    \author{HAHAH}
    \title{First title}
    \title{My title}

    \def\xxx{XXX}

    \maketitle
"""

    tokens = expander.expand(text)
    out_str = expander.convert_tokens_to_str(tokens).strip()
    print(out_str)
