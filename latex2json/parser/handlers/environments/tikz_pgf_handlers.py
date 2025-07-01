from latex2json.latex_maps.environments import PICTURE_ENVIRONMENTS
from latex2json.nodes import DiagramNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token, TokenType
from latex2json.parser.handlers.commands.command_handler_utils import (
    register_ignore_handlers_util,
)


def make_picture_handler(env_name: str):
    def picture_handler(parser: ParserCore, token: Token):
        # parse remaining env block
        tokens = parser.parse_tokens_until(
            lambda tok: tok == Token(TokenType.ENVIRONMENT_END, env_name),
            consume_predicate=True,
        )
        return [DiagramNode(env_name, parser.convert_tokens_to_str(tokens).strip())]

    return picture_handler


def register_tikz_pgf_handlers(parser: ParserCore):
    for env in PICTURE_ENVIRONMENTS:
        parser.register_env_handler(env, make_picture_handler(env))

    ignore_patterns = {
        "usetikzlibrary": 1,
        "usepgflibrary": 1,
        "usepgfplotslibrary": 1,
        "pgfplotsset": 1,
    }
    register_ignore_handlers_util(parser, ignore_patterns)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
    \def\aaa{AAA}
\begin{tikzpicture}
    \aaa
    \draw (0,0) -- (1,1);
    \draw (0,0) -- (1,1);
\end{tikzpicture}

POST
    """.strip()

    out = parser.parse(text)
    print(out)
