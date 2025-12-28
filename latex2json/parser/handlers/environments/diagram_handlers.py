from typing import List
from latex2json.latex_maps.environments import DIAGRAM_ENVIRONMENTS
from latex2json.nodes import DiagramNode
from latex2json.nodes.graphics_pdf_diagram_nodes import IncludeGraphicsNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import (
    is_begin_group_token,
    is_end_group_token,
    convert_str_to_tokens,
)


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


def make_diagram_handler(arg_spec: str):
    def diagram_command_handler(parser: ParserCore, token: Token):
        r"""\chemfig{...} or \polylongdiv{...}{...}

        Spec string can contain: * (star), [ (optional arg), { (required arg)
        e.g. "{", "{{", "[{"
        """
        parser.skip_whitespace()
        # parse all as verbatim tokens, then convert to str
        all_tokens = [token]

        for char in arg_spec:
            parser.skip_whitespace()
            if char == "*":
                # Consume star if present
                if parser.peek() and parser.peek().value == "*":
                    all_tokens.append(parser.consume())
            elif char == "[":
                # Optional bracket argument
                if parser.peek() and parser.peek().value == "[":
                    tokens = parser.parse_begin_end_as_tokens(
                        lambda t: t.value == "[",
                        lambda t: t.value == "]",
                        check_first_token=True,
                        include_begin_end_tokens=True,
                    )
                    if tokens:
                        all_tokens.extend(tokens)
            elif char == "{":
                # Required brace argument
                tokens = parser.parse_begin_end_as_tokens(
                    is_begin_group_token,
                    is_end_group_token,
                    check_first_token=True,
                    include_begin_end_tokens=True,
                )
                if not tokens:
                    break
                all_tokens.extend(tokens)

        if len(all_tokens) == 1:  # only the command token, no args parsed
            return []

        diagram_str = parser.convert_tokens_to_str(all_tokens)
        diagram_node = DiagramNode(token.value, diagram_str)
        diagram_node.source_file = token.source_file
        return [diagram_node]

    return diagram_command_handler


def xymatrix_handler(parser: ParserCore, token: Token):
    r"""\xymatrix with optional @ modifiers

    Handles xy-pic @ syntax for spacing and arrow options:
    - \xymatrix@C-2ex{...}  (reduce column spacing)
    - \xymatrix@R+1em{...}  (increase row spacing)
    - \xymatrix@C=1pc@R=2pc{...}  (set both)

    Also handles \xymatrix@ as a single token (when \makeatletter is active)
    """
    parser.skip_whitespace()

    # Check if token contains @ (e.g., "xymatrix@C" in makeatletter context)
    # If so, normalize the token and push "@" + rest back
    has_at = "@" in token.value
    if has_at:
        post_at_str = token.value.split("@", 1)[1]
        # Normalize token to just "xymatrix"
        token.value = "xymatrix"
        # Push "@" back first
        at_token_to_push = Token(TokenType.CHARACTER, "@", catcode=Catcode.OTHER)
        # Then the rest of the string
        parser.push_tokens([at_token_to_push] + convert_str_to_tokens(post_at_str))

    all_tokens = [token]

    # Consume @ options like @C-2ex, @R+1em, etc.
    while parser.peek() and parser.peek().value == "@":
        # Consume the @ token
        at_token = parser.consume()
        all_tokens.append(at_token)

        # Consume option characters (letters, digits, +, -, =, etc.) until we hit whitespace or { or another @
        while parser.peek() and parser.peek().value not in [
            " ",
            "\n",
            "\t",
            "{",
            "@",
            None,
        ]:
            opt_token = parser.consume()
            all_tokens.append(opt_token)

        parser.skip_whitespace()

    # Now parse the main brace group
    tokens = parser.parse_begin_end_as_tokens(
        is_begin_group_token,
        is_end_group_token,
        check_first_token=True,
        include_begin_end_tokens=True,
    )
    if tokens:
        all_tokens.extend(tokens)

    if len(all_tokens) == 1:  # only the command token, no braces parsed
        return []

    diagram_str = parser.convert_tokens_to_str(all_tokens)
    # Normalize env_name to "xymatrix" (strip trailing @ if present)
    env_name = "xymatrix"
    diagram_node = DiagramNode(env_name, diagram_str)
    diagram_node.source_file = token.source_file
    return [diagram_node]


def register_picture_handlers(parser: ParserCore):
    for env in DIAGRAM_ENVIRONMENTS:
        if env == "overpic":
            parser.register_env_handler(env, overpic_handler)
        else:
            parser.register_env_handler(env, make_picture_handler(env))

    other_diagrams = {
        "chemfig": "{",
        "polylongdiv": "{{",
        "pgfplotstabletypeset": "[{",
        "AddToShipoutPictureFG": "*{",
    }
    for cmd, arg_spec in other_diagrams.items():
        parser.register_handler(cmd, make_diagram_handler(arg_spec))

    # xymatrix commands
    parser.register_handler("xymatrix", xymatrix_handler)

    # Register pattern handler for xymatrix with @ options (e.g., \xymatrix@C, \xymatrix@R+2em)
    # this could happen due to \makeatletter, where the control sequence e.g. \xymatrix@C is treated as a single token
    def is_xymatrix_with_at(cmd_name: str) -> bool:
        return cmd_name.startswith("xymatrix@")

    parser.register_pattern_handler(is_xymatrix_with_at, xymatrix_handler)


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
