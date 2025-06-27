from latex2json.nodes import IncludeGraphicsNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token, TokenType


def overpic_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    options = parser.parse_bracket_as_nodes()
    parser.skip_whitespace()
    path = parser.parse_brace_name()
    if not path:
        parser.logger.warning("No path provided for overpic")
        return []

    # parse remaining env block
    tokens = parser.parse_tokens_until(
        lambda tok: tok == Token(TokenType.ENVIRONMENT_END, "overpic"),
        consume_predicate=True,
    )
    # do something with the body tokens?

    return [IncludeGraphicsNode(path)]


def register_overpic_handler(parser: ParserCore):
    parser.register_env_handler("overpic", overpic_handler)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
    \begin{overpic}[width=0.5\textwidth]{example-image}
    \put(33,29){\tiny Faster R-CNN}
    \end{overpic} 
    POST
    """.strip()

    out = parser.parse(text)
    print(out)
