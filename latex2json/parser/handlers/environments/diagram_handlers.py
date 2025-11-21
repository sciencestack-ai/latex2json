from typing import List
from latex2json.latex_maps.environments import PICTURE_ENVIRONMENTS
from latex2json.nodes import DiagramNode
from latex2json.nodes.graphics_pdf_diagram_nodes import IncludeGraphicsNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import is_begin_group_token, is_end_group_token


def make_picture_handler(env_name: str):
    def picture_handler(parser: ParserCore, token: Token) -> List[DiagramNode]:
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
        tokens = [token] + tokens + [end_token]
        diagram_node = DiagramNode(
            env_name, parser.convert_tokens_to_str(tokens).strip()
        )
        diagram_node.source_file = token.source_file
        return [diagram_node]

    return picture_handler


def overpic_handler(parser: ParserCore, token: Token):
    nodes = make_picture_handler("overpic")(parser, token)
    if not nodes:
        return []
    diagram_node = nodes[0]
    out_node = IncludeGraphicsNode("", code=diagram_node.diagram)
    out_node.source_file = diagram_node.source_file
    return [out_node]


def make_diagram_handler(num_braces: int):
    def diagram_command_handler(parser: ParserCore, token: Token):
        r"""\xymatrix{...} or \chemfig{...}"""
        parser.skip_whitespace()
        # parse all as verbatim tokens, then convert to str
        all_tokens = [token]
        for _ in range(num_braces):
            tokens = parser.parse_begin_end_as_tokens(
                is_begin_group_token,
                is_end_group_token,
                check_first_token=True,
                include_begin_end_tokens=True,
            )
            if not tokens:
                break
            all_tokens.extend(tokens)

        if len(all_tokens) == 1:  # only the command token, no braces parsed
            return []

        diagram_str = parser.convert_tokens_to_str(all_tokens)
        diagram_node = DiagramNode(token.value, diagram_str)
        diagram_node.source_file = token.source_file
        return [diagram_node]

    return diagram_command_handler


def register_picture_handlers(parser: ParserCore):
    for env in PICTURE_ENVIRONMENTS:
        if env == "overpic":
            parser.register_env_handler(env, overpic_handler)
        else:
            parser.register_env_handler(env, make_picture_handler(env))

    parser.register_handler("xymatrix", make_diagram_handler(1))
    parser.register_handler("chemfig", make_diagram_handler(1))
    parser.register_handler("polylongdiv", make_diagram_handler(2))


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
\xymatrix {
    A & B \\
    C & D
}

\polylongdiv{x^3 + 2x^2 + 3x + 4}{x + 1}
""".strip()

    out = parser.parse(text)
    print(out)
