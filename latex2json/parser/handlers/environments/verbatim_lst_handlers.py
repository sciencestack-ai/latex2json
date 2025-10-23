from latex2json.latex_maps.environments import COMMON_ENVIRONMENTS
from latex2json.nodes.base_nodes import VerbatimNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import (
    EnvironmentStartToken,
    EnvironmentType,
    Token,
    TokenType,
)


def make_verbatim_handler(env_name: str):
    def verbatim_handler(parser: ParserCore, token: Token):
        tokens = parser.parse_tokens_until(
            lambda tok: tok == Token(TokenType.ENVIRONMENT_END, env_name),
            consume_predicate=True,
        )
        if env_name == "comment":
            # ignore \begin{comment}...
            return []
        return [VerbatimNode(parser.convert_tokens_to_str(tokens).strip())]

    return verbatim_handler


def lstlisting_handler(parser: ParserCore, token: EnvironmentStartToken):
    parser.skip_whitespace()
    title = parser.parse_bracket_as_nodes() or []
    tokens = parser.parse_tokens_until(
        lambda tok: tok == Token(TokenType.ENVIRONMENT_END, "lstlisting"),
        consume_predicate=True,
    )
    if not tokens:
        return []
    return [
        VerbatimNode(
            parser.convert_tokens_to_str(tokens).strip(),
            title=parser.convert_nodes_to_str(title).strip(),
        )
    ]


def minted_handler(parser: ParserCore, token: EnvironmentStartToken):
    parser.skip_whitespace()
    tokens = parser.parse_tokens_until(
        lambda tok: tok == Token(TokenType.ENVIRONMENT_END, "minted"),
        consume_predicate=True,
    )
    if not tokens:
        return []
    title: str | None = None
    if token.args:
        title = parser.convert_tokens_to_str(token.args[0]).strip()
    return [VerbatimNode(parser.convert_tokens_to_str(tokens).strip(), title=title)]


def register_verbatim_lst_handlers(parser: ParserCore):
    for env, env_def in COMMON_ENVIRONMENTS.items():
        if env == "lstlisting":
            parser.register_env_handler(env, lstlisting_handler)
        elif env == "minted":
            parser.register_env_handler(env, minted_handler)
        elif env_def.env_type == EnvironmentType.VERBATIM:
            parser.register_env_handler(env, make_verbatim_handler(env))


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
\begin{minted}[fontsize=\small, bgcolor=gray!10]{javascript}
const x = 10;
\end{minted}
"""
    out = parser.parse(text)
    print(out)
