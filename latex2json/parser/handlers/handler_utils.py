from typing import List
from latex2json.nodes.base_nodes import ASTNode, CommandNode
from latex2json.parser.parser_core import ParserCore, Handler
from latex2json.tokens.types import Token

COMMAND_ARGS = {
    "ref": "{",  # ref requires one mandatory argument
    "label": "{",  # label requires one mandatory argument
    "cite": "*[{",  # cite can have a star, optional arg, and required arg
    "somearg": "*[{[",  # keeping this as an example
}


def make_generic_command_handler(command_name: str, arg_spec: str) -> Handler:
    """
    Generic handler for LaTeX commands based on their argument specification.
    Spec string can contain: * (star), [ (optional arg), { (required arg)
    Returns empty list if required arguments are not found.
    """

    def generic_command_handler(parser: ParserCore, token: Token) -> list:
        spec = arg_spec
        if len(spec) == 0:
            return []

        args: List[List[ASTNode]] = []
        opt_args: List[List[ASTNode]] = []
        has_star = False

        if spec[0] == "*":
            has_star = parser.parse_asterisk()
            spec = spec[1:]

        for char in spec:
            parser.skip_whitespace()
            if char == "*":
                parser.parse_asterisk()
            elif char == "[":
                opt_arg = parser.parse_bracket_as_nodes()
                if opt_arg:
                    opt_args.append(opt_arg)
            elif char == "{":
                req_arg = parser.parse_brace_as_nodes()
                if not req_arg:  # Required argument not found
                    parser.logger.warning(
                        f"Required argument not found for command {command_name}"
                    )
                    return []
                args.append(req_arg)

        return [
            CommandNode(command_name, args=args, opt_args=opt_args, has_star=has_star)
        ]

    return generic_command_handler
