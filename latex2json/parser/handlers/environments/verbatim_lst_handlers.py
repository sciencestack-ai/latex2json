from latex2json.latex_maps.environments import COMMON_ENVIRONMENTS
from latex2json.nodes.base_nodes import VerbatimNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import EnvironmentType, Token, TokenType


def make_verbatim_handler(env_name: str):
    def verbatim_handler(parser: ParserCore, token: Token):
        tokens = parser.parse_tokens_until(
            lambda tok: tok == Token(TokenType.ENVIRONMENT_END, env_name),
            consume_predicate=True,
        )
        return [VerbatimNode(parser.convert_tokens_to_str(tokens).strip())]

    return verbatim_handler


def lstlisting_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    title = parser.parse_bracket_as_nodes() or []
    tokens = parser.parse_tokens_until(
        lambda tok: tok == Token(TokenType.ENVIRONMENT_END, "lstlisting"),
        consume_predicate=True,
    )
    return [
        VerbatimNode(
            parser.convert_tokens_to_str(tokens).strip(),
            title=parser.convert_nodes_to_str(title).strip(),
        )
    ]


def register_verbatim_lst_handlers(parser: ParserCore):
    for env, env_def in COMMON_ENVIRONMENTS.items():
        if env == "lstlisting":
            parser.register_env_handler(env, lstlisting_handler)
        elif env_def.env_type == EnvironmentType.VERBATIM:
            parser.register_env_handler(env, make_verbatim_handler(env))


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"\begin{verbatim}Hello\end{verbatim}"
    out = parser.parse(text)
    print(out)
