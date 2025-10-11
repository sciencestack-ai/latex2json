from typing import List
from latex2json.latex_maps.environments import PICTURE_ENVIRONMENTS
from latex2json.nodes import DiagramNode
from latex2json.nodes.graphics_pdf_diagram_nodes import IncludeGraphicsNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import is_begin_group_token, is_end_group_token


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


def diagram_command_handler(parser: ParserCore, token: Token):
    r"""\xymatrix{...} or \chemfig{...}"""
    parser.skip_whitespace()
    # parse all as verbatim tokens, then convert to str
    tokens = parser.parse_begin_end_as_tokens(
        is_begin_group_token,
        is_end_group_token,
        check_first_token=True,
        include_begin_end_tokens=True,
    )
    if not tokens:
        return []
    diagram_str = parser.convert_tokens_to_str([token] + tokens)

    return [DiagramNode(token.value, diagram_str)]


def register_picture_handlers(parser: ParserCore):
    for env in PICTURE_ENVIRONMENTS:
        if env == "overpic":
            parser.register_env_handler(env, overpic_handler)
        else:
            parser.register_env_handler(env, make_picture_handler(env))

    parser.register_handler("xymatrix", diagram_command_handler)
    parser.register_handler("chemfig", diagram_command_handler)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
\xymatrix {
    A & B \\
    C & D
}
""".strip()

    out = parser.parse(text)
    print(out)
