from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import wrap_tokens_in_braces, wrap_tokens_in_brackets


def is_semicolon_token(tok: Token) -> bool:
    return tok == Token(TokenType.CHARACTER, ";", catcode=Catcode.OTHER)


def tikz_cmd_handler(expander: ExpanderCore, token: Token):
    # parse tokens verbatim up to ;
    expander.skip_whitespace()
    options = expander.parse_bracket_as_tokens() or []
    expander.skip_whitespace()
    tokens = expander.parse_brace_as_tokens(verbatim=True)
    if tokens is None:
        tokens = expander.parse_tokens_until(
            is_semicolon_token, consume_predicate=True, verbatim=True
        )
        if not tokens:
            expander.logger.warning("No tokens found for \\tikz command")
            return None

        # append semicolon to the end of the tokens
        tokens.append(Token(TokenType.CHARACTER, ";", catcode=Catcode.OTHER))
    else:
        tokens = wrap_tokens_in_braces(tokens)

    env_name_tokens = expander.convert_str_to_tokens("{tikzpicture}")

    if options:
        options = wrap_tokens_in_brackets(options)

    # push as \begin{tikzpicture} ... \end{tikzpicture}
    out_tokens = [
        Token(TokenType.CONTROL_SEQUENCE, "begin"),
        *env_name_tokens,
        *options,
        *tokens,
        Token(TokenType.CONTROL_SEQUENCE, "end"),
        *env_name_tokens,
    ]
    expander.push_tokens(out_tokens)
    return []


def register_tikz_pgf_handlers(expander: ExpanderCore):
    expander.register_handler("tikz", tikz_cmd_handler, is_global=True)

    ignore_patterns = {
        "usetikzlibrary": 1,
        "tikzset": 1,
        "tikzcdset": 1,
        "usepgflibrary": 1,
        "usepgfplotslibrary": 1,
        "pgfplotsset": 1,
        "pgfdeclareshape": 2,
    }

    register_ignore_handlers_util(expander, ignore_patterns)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_tikz_pgf_handlers(expander)

    text = r"""
% braced

\def\xxx{XXX}
\tikz[baseline=(A.base)]{\node[opacity=-1](A) {The}; \xxx
				\shade[inner color=blue!100] (A.south east) rectangle (A.north west);
				\path (A.center)
                  \pgfextra{\pgftext{The}};
}

% no brace
\tikz\fill[natural] (0,0) circle (.5ex);
"""

    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
