from typing import List
from latex2json.latex_maps.environments import PICTURE_ENVIRONMENTS
from latex2json.nodes import DiagramNode
from latex2json.nodes.graphics_pdf_diagram_nodes import IncludeGraphicsNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token, TokenType
from latex2json.parser.handlers.commands.command_handler_utils import (
    register_ignore_handlers_util,
)


def make_picture_handler(env_name: str):
    def picture_handler(parser: ParserCore, start_token: Token) -> List[DiagramNode]:
        # parse remaining env block
        def is_end_token(tok: Token):
            return tok.type == TokenType.ENVIRONMENT_END and tok.value == env_name

        tokens = parser.parse_tokens_until(
            is_end_token,
            consume_predicate=False,
        )
        end_token = parser.consume()
        if not tokens:
            return []
        tokens = [start_token] + tokens + [end_token]
        return [DiagramNode(env_name, parser.convert_tokens_to_str(tokens).strip())]

    return picture_handler


def overpic_handler(parser: ParserCore, token: Token):
    nodes = make_picture_handler("overpic")(parser, token)
    if not nodes:
        return []
    diagram_node = nodes[0]

    return [IncludeGraphicsNode("", code=diagram_node.diagram)]


def register_picture_handlers(parser: ParserCore):
    for env in PICTURE_ENVIRONMENTS:
        if env == "overpic":
            parser.register_env_handler(env, overpic_handler)
        else:
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

    text = r"""
    \begin{overpic}[width=0.5\textwidth]{example-image}
    \put(33,29){\tiny Faster R-CNN}
    \end{overpic} 
    """.strip()

    out = parser.parse(text)
    print(out)
