from latex2json.nodes.base_nodes import VerbatimNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token, TokenType


def verbatim_handler(parser: ParserCore, token: Token):
    tokens = parser.parse_tokens_until(
        lambda tok: tok == Token(TokenType.ENVIRONMENT_END, "verbatim"),
        consume_predicate=True,
    )
    return [VerbatimNode(parser.convert_tokens_to_str(tokens).strip())]


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
    parser.register_env_handler("verbatim", verbatim_handler)
    parser.register_env_handler("lstlisting", lstlisting_handler)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"\begin{verbatim}Hello\end{verbatim}"
    out = parser.parse(text)
    print(out)
