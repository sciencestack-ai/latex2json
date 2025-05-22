from dataclasses import dataclass
from typing import List, Optional, Tuple
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.utils import substitute_token_args
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import is_begin_bracket_token


@dataclass
class NewCommandResult:
    name: str
    definition: List[Token]
    num_args: int
    default_arg: Optional[List[Token]] = None


def get_parsed_args_from_newcommand(
    expander: ExpanderCore, num_args: int, default_arg: Optional[List[Token]] = None
) -> List[List[Token]]:
    if num_args > 0:
        # e.g. \cmd {arg}
        expander.skip_whitespace()
    args: List[List[Token]] = []

    if default_arg:
        tok = expander.peek()
        # if the next token is a begin bracket, replace the default arg with the parsed bracket
        if tok and is_begin_bracket_token(tok):
            default_arg = expander.parse_bracket_as_tokens()

        args.append(default_arg)
        num_args -= 1

    for i in range(num_args):
        expander.skip_whitespace()
        tokens = expander.parse_immediate_token()
        if tokens is None:
            expander.logger.warning(
                f"Warning: expected argument {i+1} but found nothing"
            )
            return None
        args.append(tokens)

    return args


class NewCommandMacro(Macro):
    def __init__(self, name: str, allow_redefine: bool = False):
        super().__init__(name)
        self.allow_redefine = allow_redefine
        self.handler = lambda expander, node: self._expand(expander, node)

    def _expand(self, expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        out = newcommand_handler(expander, token, self.allow_redefine)
        if out is None:
            return None

        def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
            # Parse exactly num_args arguments
            args = get_parsed_args_from_newcommand(
                expander, out.num_args, out.default_arg
            )
            if args is None:
                return None

            subbed = substitute_token_args(out.definition, args, math_mode=False)
            expander.push_tokens(subbed)
            return []

        macro = Macro(out.name, handler, out.definition)
        expander.register_macro(out.name, macro, is_global=True)

        return []


def get_newcommand_name(expander: ExpanderCore) -> Optional[str]:
    expander.parse_asterisk()
    expander.skip_whitespace()

    # Parse command name
    cmd = expander.parse_immediate_token()
    if (
        not cmd
        or len(cmd) < 0
        or len(cmd) > 1
        or cmd[0].type != TokenType.CONTROL_SEQUENCE
    ):
        expander.logger.warning(
            f"Warning: \\newcommand expects a command name, but found {cmd}"
        )
        return None

    name = cmd[0].value

    return name


def get_newcommand_args_and_definition(
    expander: ExpanderCore,
) -> Tuple[int, Optional[List[Token]], List[Token]]:
    # Parse optional number of arguments [n]
    num_args = 0
    default_arg = None

    expander.skip_whitespace()
    tok = expander.peek()
    if tok and is_begin_bracket_token(tok):
        arg_tokens = expander.parse_bracket_as_tokens()
        try:
            num_args = int("".join(t.value for t in arg_tokens))
        except ValueError:
            expander.logger.warning(
                f"Warning: invalid number of arguments: {''.join(t.value for t in arg_tokens)}"
            )
            return None

        # Parse optional default value for first argument
        expander.skip_whitespace()
        tok = expander.peek()
        if tok and is_begin_bracket_token(tok):
            default_arg = expander.parse_bracket_as_tokens()

    # Parse command definition
    expander.skip_whitespace()
    definition = expander.parse_brace_as_tokens()

    if definition is None:
        expander.logger.warning(f"Warning: expects a definition in braces")
        return None

    return (num_args, default_arg, definition)


def newcommand_handler(
    expander: ExpanderCore, token: Token, allow_redefine: bool
) -> Optional[NewCommandResult]:
    name = get_newcommand_name(expander)
    if name is None:
        return None

    # Check if command already exists
    if not allow_redefine and expander.state.get_macro(name):
        expander.logger.warning(
            f"Warning: command {name} already exists. Use \\renewcommand to redefine"
        )
        return None

    out = get_newcommand_args_and_definition(expander)
    if out is None:
        return None

    num_args, default_arg, definition = out

    return NewCommandResult(
        name=name, definition=definition, num_args=num_args, default_arg=default_arg
    )


def register_newcommand(expander: ExpanderCore):
    expander.register_macro(
        "\\newcommand",
        NewCommandMacro("\\newcommand", allow_redefine=False),
        is_global=True,
    )
    expander.register_macro(
        "\\renewcommand",
        NewCommandMacro("\\renewcommand", allow_redefine=True),
        is_global=True,
    )


if __name__ == "__main__":
    expander = ExpanderCore()
    register_newcommand(expander)

    # # Basic command
    # expander.expand(r"\newcommand{\hello}{Hello, world!}")
    # print(expander.expand(r"\hello"))

    # # Command with arguments
    # expander.expand(r"\newcommand{\greet}[2]{Hello #1 and #2!}")
    # out = expander.expand(r"\greet{Alice}{Bob}")

    # Command with default argument
    expander.expand(r"\newcommand\welcome[1][friend]{Hello, #1!}")
    out = expander.expand(r"\welcome{Alice}")  # Uses provided argument
