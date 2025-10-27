r"""
Handler for LaTeX3 xparse commands like \NewDocumentCommand, \DeclareDocumentCommand, etc.

The xparse package provides powerful argument parsing with specifications like:
- s: star (optional, produces TF boolean)
- m: mandatory braced argument
- o: optional argument in []
- O{default}: optional argument with default value
- d(): optional delimited argument
- g: optional argument in {}
- G{default}: optional braced argument with default
- v: verbatim argument
- etc.
"""

from dataclasses import dataclass
from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import (
    is_begin_bracket_token,
    is_begin_group_token,
    is_whitespace_token,
)


@dataclass
class ArgSpec:
    """Represents a single argument specification."""

    spec_type: str  # 's', 'm', 'o', 'O', 'd', 'g', 'G', 'v', etc.
    default_value: Optional[List[Token]] = None
    delimiters: Optional[tuple[str, str]] = None  # For delimited arguments like d()

    def __repr__(self):
        if self.default_value:
            return f"{self.spec_type}{{default}}"
        elif self.delimiters:
            return f"{self.spec_type}{self.delimiters[0]}{self.delimiters[1]}"
        return self.spec_type


@dataclass
class XparseResult:
    cmd_token: Token
    arg_specs: List[ArgSpec]
    definition: List[Token]


def parse_argument_specification(expander: ExpanderCore) -> Optional[List[ArgSpec]]:
    """
    Parse xparse argument specification like { s O{default} m }

    Returns list of ArgSpec objects.
    """
    arg_spec_tokens = expander.parse_brace_as_tokens()
    if arg_spec_tokens is None:
        return None

    specs: List[ArgSpec] = []
    i = 0

    while i < len(arg_spec_tokens):
        tok = arg_spec_tokens[i]

        # Skip whitespace
        if is_whitespace_token(tok):
            i += 1
            continue

        spec_char = tok.value

        # Star argument (optional)
        if spec_char == "s":
            specs.append(ArgSpec(spec_type="s"))
            i += 1

        # Mandatory argument
        elif spec_char == "m":
            specs.append(ArgSpec(spec_type="m"))
            i += 1

        # Optional argument without default
        elif spec_char == "o":
            specs.append(ArgSpec(spec_type="o"))
            i += 1

        # Optional argument with default O{default}
        elif spec_char == "O":
            i += 1
            # Next should be a brace group with default value
            if i < len(arg_spec_tokens) and is_begin_group_token(arg_spec_tokens[i]):
                # Find matching closing brace
                depth = 1
                i += 1
                default_tokens = []
                while i < len(arg_spec_tokens) and depth > 0:
                    if is_begin_group_token(arg_spec_tokens[i]):
                        depth += 1
                        if depth > 1:
                            default_tokens.append(arg_spec_tokens[i])
                    elif (
                        arg_spec_tokens[i].value == "}"
                        and arg_spec_tokens[i].type == TokenType.CHARACTER
                    ):
                        depth -= 1
                        if depth > 0:
                            default_tokens.append(arg_spec_tokens[i])
                    else:
                        default_tokens.append(arg_spec_tokens[i])
                    i += 1
                specs.append(ArgSpec(spec_type="O", default_value=default_tokens))
            else:
                expander.logger.warning(
                    "O argument spec requires default value in braces"
                )
                return None

        # Optional braced argument
        elif spec_char == "g":
            specs.append(ArgSpec(spec_type="g"))
            i += 1

        # Optional braced argument with default G{default}
        elif spec_char == "G":
            i += 1
            if i < len(arg_spec_tokens) and is_begin_group_token(arg_spec_tokens[i]):
                depth = 1
                i += 1
                default_tokens = []
                while i < len(arg_spec_tokens) and depth > 0:
                    if is_begin_group_token(arg_spec_tokens[i]):
                        depth += 1
                        if depth > 1:
                            default_tokens.append(arg_spec_tokens[i])
                    elif (
                        arg_spec_tokens[i].value == "}"
                        and arg_spec_tokens[i].type == TokenType.CHARACTER
                    ):
                        depth -= 1
                        if depth > 0:
                            default_tokens.append(arg_spec_tokens[i])
                    else:
                        default_tokens.append(arg_spec_tokens[i])
                    i += 1
                specs.append(ArgSpec(spec_type="G", default_value=default_tokens))
            else:
                expander.logger.warning(
                    "G argument spec requires default value in braces"
                )
                return None

        # Delimited optional argument d()
        elif spec_char == "d":
            i += 1
            if i + 1 < len(arg_spec_tokens):
                open_delim = arg_spec_tokens[i].value
                close_delim = arg_spec_tokens[i + 1].value
                specs.append(
                    ArgSpec(spec_type="d", delimiters=(open_delim, close_delim))
                )
                i += 2
            else:
                expander.logger.warning(
                    "d argument spec requires two delimiter characters"
                )
                return None

        # Verbatim argument
        elif spec_char == "v":
            specs.append(ArgSpec(spec_type="v"))
            i += 1

        else:
            # Unknown spec, skip
            expander.logger.warning(f"Unknown argument spec: {spec_char}")
            i += 1

    return specs


def parse_xparse_arguments(
    expander: ExpanderCore, arg_specs: List[ArgSpec]
) -> Optional[List[Optional[List[Token]]]]:
    """
    Parse arguments according to xparse specification.

    Returns list where each element is either:
    - List[Token]: the parsed argument
    - None: for missing optional arguments
    - [Token(value='-NoValue-')]: special marker for missing optionals
    """
    parsed_args: List[Optional[List[Token]]] = []

    for spec in arg_specs:
        if spec.spec_type == "s":
            # Star argument - check for *
            expander.skip_whitespace()
            has_star = expander.parse_asterisk()
            # Store as special boolean marker
            if has_star:
                parsed_args.append([Token(TokenType.CHARACTER, "TrueBooleanValue")])
            else:
                parsed_args.append([Token(TokenType.CHARACTER, "FalseBooleanValue")])

        elif spec.spec_type == "m":
            # Mandatory argument
            expander.skip_whitespace()
            arg = expander.parse_immediate_token()
            if arg is None:
                expander.logger.warning("Expected mandatory argument")
                return None
            parsed_args.append(arg)

        elif spec.spec_type == "o":
            # Optional argument in []
            expander.skip_whitespace()
            tok = expander.peek()
            if tok and is_begin_bracket_token(tok):
                arg = expander.parse_bracket_as_tokens()
                parsed_args.append(arg)
            else:
                # Missing optional argument - use special marker
                parsed_args.append([Token(TokenType.CHARACTER, "-NoValue-")])

        elif spec.spec_type == "O":
            # Optional argument with default
            expander.skip_whitespace()
            tok = expander.peek()
            if tok and is_begin_bracket_token(tok):
                arg = expander.parse_bracket_as_tokens()
                parsed_args.append(arg)
            else:
                # Use default value
                parsed_args.append(spec.default_value if spec.default_value else [])

        elif spec.spec_type == "g":
            # Optional braced argument
            expander.skip_whitespace()
            tok = expander.peek()
            if tok and is_begin_group_token(tok):
                arg = expander.parse_brace_as_tokens()
                parsed_args.append(arg)
            else:
                parsed_args.append([Token(TokenType.CHARACTER, "-NoValue-")])

        elif spec.spec_type == "G":
            # Optional braced argument with default
            expander.skip_whitespace()
            tok = expander.peek()
            if tok and is_begin_group_token(tok):
                arg = expander.parse_brace_as_tokens()
                parsed_args.append(arg)
            else:
                parsed_args.append(spec.default_value if spec.default_value else [])

        elif spec.spec_type == "d":
            # Delimited optional argument
            expander.skip_whitespace()
            open_delim, close_delim = spec.delimiters
            tok = expander.peek()
            if tok and tok.value == open_delim:
                expander.consume()  # consume open delimiter
                arg = expander.parse_tokens_until(lambda t: t.value == close_delim)
                expander.consume()  # consume close delimiter
                parsed_args.append(arg)
            else:
                parsed_args.append([Token(TokenType.CHARACTER, "-NoValue-")])

        elif spec.spec_type == "v":
            # Verbatim argument - read until next delimiter
            expander.skip_whitespace()
            arg = expander.parse_immediate_token()
            if arg:
                parsed_args.append(arg)
            else:
                parsed_args.append([])

        else:
            # Unknown spec type
            parsed_args.append([])

    return parsed_args


class NewDocumentCommandMacro(Macro):
    def __init__(self, name: str, allow_redefine: bool = True):
        super().__init__(name)
        self.allow_redefine = allow_redefine
        self.handler = lambda expander, node: self._expand(expander, node)
        self.type = MacroType.DECLARATION

    def _expand(self, expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        out = newdocumentcommand_handler(expander, token, self.allow_redefine)
        if out is None:
            return None

        def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
            # Parse arguments according to xparse specification
            args = parse_xparse_arguments(expander, out.arg_specs)
            if args is None:
                return None

            # Substitute arguments into definition
            subbed = expander.substitute_token_args(out.definition, args)
            expander.push_tokens(subbed)
            return []

        macro = Macro(out.cmd_token, handler, out.definition)
        expander.register_macro(
            out.cmd_token, macro, is_global=True, is_user_defined=True
        )

        return []


def newdocumentcommand_handler(
    expander: ExpanderCore, token: Token, allow_redefine: bool = True
) -> Optional[XparseResult]:
    r"""
    Handle \NewDocumentCommand{\cmd}{arg_spec}{definition}
    """
    # Parse command name
    cmd = expander.parse_command_name_token()
    if cmd is None:
        expander.logger.warning(
            f"\\NewDocumentCommand expects a command name, but found {expander.peek()}"
        )
        return None

    cmd.value = cmd.value.strip()

    # Check if command already exists
    if not allow_redefine and expander.get_macro(cmd):
        expander.logger.info(
            f"command {cmd.value} already exists. Use \\RenewDocumentCommand to redefine"
        )
        return None

    # Parse argument specification
    expander.skip_whitespace()
    arg_specs = parse_argument_specification(expander)
    if arg_specs is None:
        expander.logger.warning(
            f"\\NewDocumentCommand {cmd.value} expects an argument specification in braces"
        )
        return None

    # Parse definition
    expander.skip_whitespace()
    definition = expander.parse_immediate_token()
    if definition is None:
        expander.logger.warning(
            f"\\NewDocumentCommand {cmd.value} expects a definition in braces"
        )
        return None

    return XparseResult(
        cmd_token=cmd,
        arg_specs=arg_specs,
        definition=definition,
    )


def register_ifboolean_commands(expander: ExpanderCore):
    r"""
    Register \IfBooleanTF, \IfBooleanT, \IfBooleanF commands.

    These check if an argument is the special boolean value from a star argument.
    """

    def ifboolean_tf_handler(
        expander: ExpanderCore, _token: Token
    ) -> Optional[List[Token]]:
        # Parse the argument to test (should be #1, #2, etc.)
        arg_to_test = expander.parse_immediate_token(skip_whitespace=True)
        if not arg_to_test:
            return None

        # Parse true branch
        true_branch = expander.parse_immediate_token(skip_whitespace=True)
        if not true_branch:
            return None

        # Parse false branch
        false_branch = expander.parse_immediate_token(skip_whitespace=True)
        if not false_branch:
            return None

        # Check if argument is TrueBooleanValue
        if len(arg_to_test) == 1 and arg_to_test[0].value == "TrueBooleanValue":
            expander.push_tokens(true_branch)
        else:
            expander.push_tokens(false_branch)

        return []

    def ifboolean_t_handler(
        expander: ExpanderCore, _token: Token
    ) -> Optional[List[Token]]:
        arg_to_test = expander.parse_immediate_token(skip_whitespace=True)
        if not arg_to_test:
            return None

        true_branch = expander.parse_immediate_token(skip_whitespace=True)
        if not true_branch:
            return None

        if len(arg_to_test) == 1 and arg_to_test[0].value == "TrueBooleanValue":
            expander.push_tokens(true_branch)

        return []

    def ifboolean_f_handler(
        expander: ExpanderCore, _token: Token
    ) -> Optional[List[Token]]:
        arg_to_test = expander.parse_immediate_token(skip_whitespace=True)
        if not arg_to_test:
            return None

        false_branch = expander.parse_immediate_token(skip_whitespace=True)
        if not false_branch:
            return None

        if len(arg_to_test) == 1 and arg_to_test[0].value != "TrueBooleanValue":
            expander.push_tokens(false_branch)

        return []

    expander.register_handler("\\IfBooleanTF", ifboolean_tf_handler, is_global=True)
    expander.register_handler("\\IfBooleanT", ifboolean_t_handler, is_global=True)
    expander.register_handler("\\IfBooleanF", ifboolean_f_handler, is_global=True)


def register_xparse(expander: ExpanderCore):
    """Register xparse commands."""
    expander.register_macro(
        "\\NewDocumentCommand",
        NewDocumentCommandMacro("\\NewDocumentCommand", allow_redefine=True),
        is_global=True,
    )
    expander.register_macro(
        "\\RenewDocumentCommand",
        NewDocumentCommandMacro("\\RenewDocumentCommand", allow_redefine=True),
        is_global=True,
    )
    expander.register_macro(
        "\\ProvideDocumentCommand",
        NewDocumentCommandMacro("\\ProvideDocumentCommand", allow_redefine=True),
        is_global=True,
    )
    expander.register_macro(
        "\\DeclareDocumentCommand",
        NewDocumentCommandMacro("\\DeclareDocumentCommand", allow_redefine=True),
        is_global=True,
    )

    # Register IfBoolean conditionals
    register_ifboolean_commands(expander)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_xparse(expander)

    # Test basic command with star and optional argument
    expander.expand(
        r"""
    \NewDocumentCommand{\test}{ s O{default} m }{%
      \IfBooleanTF{#1}{Star}{No star}:
      #2 and #3%
    }
    """
    )

    # Test with star
    print("With star:")
    result = expander.expand(r"\test*{world}")
    print(result)

    # Test without star, with optional
    print("\nWithout star, with optional:")
    result = expander.expand(r"\test[hello]{world}")
    print(result)

    # Test without star, without optional (use default)
    print("\nWithout star, without optional:")
    result = expander.expand(r"\test{world}")
    print(result)
