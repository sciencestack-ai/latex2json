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
- e{tokens}: embellishment arguments (e.g., e{_^} for subscript/superscript)
- etc.

Supported conditionals:
- \IfBooleanTF, \IfBooleanT, \IfBooleanF: check star arguments
- \IfValueTF, \IfValueT, \IfValueF: check if optional arguments have values
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


# Sentinel token for missing optional arguments. Uses a CONTROL_SEQUENCE so that
# if it leaks through without an \IfNoValueTF guard, it won't render as visible text.
NOVALUE_TOKEN = Token(TokenType.CONTROL_SEQUENCE, "q__xparse_no_value")


def _is_novalue(tokens: List[Token]) -> bool:
    """Check if a token list is the -NoValue- sentinel."""
    return (
        len(tokens) == 1
        and tokens[0].type == TokenType.CONTROL_SEQUENCE
        and tokens[0].value == "q__xparse_no_value"
    )


def _make_novalue_token() -> List[Token]:
    """Create a fresh -NoValue- sentinel token list."""
    return [Token(TokenType.CONTROL_SEQUENCE, "q__xparse_no_value")]


@dataclass
class ArgSpec:
    """Represents a single argument specification."""

    spec_type: str  # 's', 'm', 'o', 'O', 'd', 'g', 'G', 'v', 'e', etc.
    default_value: Optional[List[Token]] = None
    delimiters: Optional[tuple[str, str]] = None  # For delimited arguments like d()
    embellishments: Optional[List[str]] = None  # For e{_^} style embellishments

    def __repr__(self):
        if self.default_value:
            return f"{self.spec_type}{{default}}"
        elif self.delimiters:
            return f"{self.spec_type}{self.delimiters[0]}{self.delimiters[1]}"
        elif self.embellishments:
            return f"{self.spec_type}{{{','.join(self.embellishments)}}}"
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

        # Embellishment argument e{_^}
        elif spec_char == "e":
            i += 1
            if i < len(arg_spec_tokens) and is_begin_group_token(arg_spec_tokens[i]):
                # Parse the embellishment characters
                i += 1
                embellishment_chars = []
                while i < len(arg_spec_tokens) and arg_spec_tokens[i].value != "}":
                    char = arg_spec_tokens[i].value
                    if char not in [" ", "\t", "\n"]:  # Skip whitespace
                        embellishment_chars.append(char)
                    i += 1
                if i < len(arg_spec_tokens):
                    i += 1  # Skip closing brace
                specs.append(ArgSpec(spec_type="e", embellishments=embellishment_chars))
            else:
                expander.logger.warning(
                    "e argument spec requires embellishment characters in braces"
                )
                return None

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
                parsed_args.append(_make_novalue_token())

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
                parsed_args.append(_make_novalue_token())

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
                parsed_args.append(_make_novalue_token())

        elif spec.spec_type == "v":
            # Verbatim argument - read until next delimiter
            expander.skip_whitespace()
            arg = expander.parse_immediate_token()
            if arg:
                parsed_args.append(arg)
            else:
                parsed_args.append([])

        elif spec.spec_type == "e":
            # Embellishment arguments - parse all embellishments that appear
            # e{_^} means #1 = subscript (_), #2 = superscript (^)
            # They can appear in any order in the input

            # First, collect all embellishments that are present
            found_embellishments = {}

            while True:
                expander.skip_whitespace()
                tok = expander.peek()
                if tok and tok.value in spec.embellishments:
                    embellishment_char = tok.value
                    expander.consume()  # consume the embellishment character
                    # Parse the argument following the embellishment
                    arg = expander.parse_immediate_token()
                    if arg:
                        found_embellishments[embellishment_char] = arg
                    else:
                        found_embellishments[embellishment_char] = [
                            Token(TokenType.CHARACTER, "-NoValue-")
                        ]
                else:
                    # No more embellishments found
                    break

            # Now assign each embellishment to its corresponding argument slot
            # based on the order in the spec
            for embellishment_char in spec.embellishments:
                if embellishment_char in found_embellishments:
                    parsed_args.append(found_embellishments[embellishment_char])
                else:
                    parsed_args.append(_make_novalue_token())

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
        if arg_to_test is None:
            return None

        # Parse true branch
        true_branch = expander.parse_immediate_token(skip_whitespace=True)
        if true_branch is None:
            return None

        # Parse false branch
        false_branch = expander.parse_immediate_token(skip_whitespace=True)
        if false_branch is None:
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
        if arg_to_test is None:
            return None

        true_branch = expander.parse_immediate_token(skip_whitespace=True)
        if true_branch is None:
            return None

        if len(arg_to_test) == 1 and arg_to_test[0].value == "TrueBooleanValue":
            expander.push_tokens(true_branch)

        return []

    def ifboolean_f_handler(
        expander: ExpanderCore, _token: Token
    ) -> Optional[List[Token]]:
        arg_to_test = expander.parse_immediate_token(skip_whitespace=True)
        if arg_to_test is None:
            return None

        false_branch = expander.parse_immediate_token(skip_whitespace=True)
        if false_branch is None:
            return None

        if len(arg_to_test) == 1 and arg_to_test[0].value != "TrueBooleanValue":
            expander.push_tokens(false_branch)

        return []

    expander.register_handler("\\IfBooleanTF", ifboolean_tf_handler, is_global=True)
    expander.register_handler("\\IfBooleanT", ifboolean_t_handler, is_global=True)
    expander.register_handler("\\IfBooleanF", ifboolean_f_handler, is_global=True)


def register_ifvalue_commands(expander: ExpanderCore):
    r"""
    Register \IfValueTF, \IfValueT, \IfValueF commands.

    These check if an argument has a value (i.e., is not -NoValue-).
    """

    def ifvalue_tf_handler(
        expander: ExpanderCore, _token: Token
    ) -> Optional[List[Token]]:
        # Parse the argument to test (should be #1, #2, etc.)
        arg_to_test = expander.parse_immediate_token(skip_whitespace=True)
        if arg_to_test is None:
            return None

        # Parse true branch
        true_branch = expander.parse_immediate_token(skip_whitespace=True)
        if true_branch is None:
            return None

        # Parse false branch
        false_branch = expander.parse_immediate_token(skip_whitespace=True)
        if false_branch is None:
            return None

        # Check if argument is NOT -NoValue-
        has_value = not (_is_novalue(arg_to_test))
        if has_value:
            expander.push_tokens(true_branch)
        else:
            expander.push_tokens(false_branch)

        return []

    def ifvalue_t_handler(
        expander: ExpanderCore, _token: Token
    ) -> Optional[List[Token]]:
        arg_to_test = expander.parse_immediate_token(skip_whitespace=True)
        if arg_to_test is None:
            return None

        true_branch = expander.parse_immediate_token(skip_whitespace=True)
        if true_branch is None:
            return None

        has_value = not (_is_novalue(arg_to_test))
        if has_value:
            expander.push_tokens(true_branch)

        return []

    def ifvalue_f_handler(
        expander: ExpanderCore, _token: Token
    ) -> Optional[List[Token]]:
        arg_to_test = expander.parse_immediate_token(skip_whitespace=True)
        if arg_to_test is None:
            return None

        false_branch = expander.parse_immediate_token(skip_whitespace=True)
        if false_branch is None:
            return None

        has_value = not (_is_novalue(arg_to_test))
        if not has_value:
            expander.push_tokens(false_branch)

        return []

    expander.register_handler("\\IfValueTF", ifvalue_tf_handler, is_global=True)
    expander.register_handler("\\IfValueT", ifvalue_t_handler, is_global=True)
    expander.register_handler("\\IfValueF", ifvalue_f_handler, is_global=True)

    # \IfNoValueTF is the inverse of \IfValueTF
    def ifnovalue_tf_handler(
        expander: ExpanderCore, _token: Token
    ) -> Optional[List[Token]]:
        arg_to_test = expander.parse_immediate_token(skip_whitespace=True)
        if arg_to_test is None:
            return None
        true_branch = expander.parse_immediate_token(skip_whitespace=True)
        if true_branch is None:
            return None
        false_branch = expander.parse_immediate_token(skip_whitespace=True)
        if false_branch is None:
            return None

        is_novalue = _is_novalue(arg_to_test)
        expander.push_tokens(true_branch if is_novalue else false_branch)
        return []

    def ifnovalue_t_handler(
        expander: ExpanderCore, _token: Token
    ) -> Optional[List[Token]]:
        arg_to_test = expander.parse_immediate_token(skip_whitespace=True)
        if arg_to_test is None:
            return None
        true_branch = expander.parse_immediate_token(skip_whitespace=True)
        if true_branch is None:
            return None

        if _is_novalue(arg_to_test):
            expander.push_tokens(true_branch)
        return []

    def ifnovalue_f_handler(
        expander: ExpanderCore, _token: Token
    ) -> Optional[List[Token]]:
        arg_to_test = expander.parse_immediate_token(skip_whitespace=True)
        if arg_to_test is None:
            return None
        false_branch = expander.parse_immediate_token(skip_whitespace=True)
        if false_branch is None:
            return None

        if not (_is_novalue(arg_to_test)):
            expander.push_tokens(false_branch)
        return []

    expander.register_handler("\\IfNoValueTF", ifnovalue_tf_handler, is_global=True)
    expander.register_handler("\\IfNoValueT", ifnovalue_t_handler, is_global=True)
    expander.register_handler("\\IfNoValueF", ifnovalue_f_handler, is_global=True)


class NewDocumentEnvironmentMacro(Macro):
    """Handler for \\NewDocumentEnvironment{env}{argspec}{begin}{end}"""

    def __init__(self, name: str, allow_redefine: bool = True):
        super().__init__(name)
        self.allow_redefine = allow_redefine
        self.handler = lambda expander, node: self._expand(expander, node)
        self.type = MacroType.DECLARATION

    def _expand(self, expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        from latex2json.latex_maps.environments import EnvironmentDefinition

        # Parse environment name
        expander.skip_whitespace()
        env_name = expander.parse_brace_name()
        if env_name is None:
            expander.logger.warning(
                f"{self.name} expects an environment name"
            )
            return None

        # Check if environment already exists
        if not self.allow_redefine and expander.get_environment_definition(env_name):
            expander.logger.info(
                f"environment {env_name} already exists"
            )
            return None

        # Parse argument specification
        expander.skip_whitespace()
        arg_specs = parse_argument_specification(expander)
        if arg_specs is None:
            expander.logger.warning(
                f"{self.name} {env_name} expects an argument specification"
            )
            return None

        # Parse begin definition
        expander.skip_whitespace()
        begin_definition = expander.parse_brace_as_tokens()
        if begin_definition is None:
            expander.logger.warning(
                f"{self.name} {env_name} expects a begin definition"
            )
            return None

        # Parse end definition
        expander.skip_whitespace()
        end_definition = expander.parse_brace_as_tokens()
        if end_definition is None:
            expander.logger.warning(
                f"{self.name} {env_name} expects an end definition"
            )
            return None

        # Count mandatory args for num_args (xparse args that consume input)
        num_args = len(arg_specs)

        # Determine default_arg: if first spec is optional, set default_arg
        default_arg = None
        if arg_specs and arg_specs[0].spec_type in ("o", "O", "g", "G", "d", "s"):
            default_arg = []

        # Create environment definition with begin_definition containing
        # both the arg parsing logic and the user's begin code
        captured_arg_specs = arg_specs
        captured_begin_def = begin_definition
        captured_end_def = end_definition

        # We create an environment with a custom begin_handler that does
        # xparse-style argument parsing, then substitutes into the definition
        def env_begin_handler(expander, token):
            from latex2json.expander.handlers.environment.environment_utils import (
                process_environment_begin,
            )

            # Parse xparse arguments
            args = parse_xparse_arguments(expander, captured_arg_specs)
            if args is None:
                args = []

            # Substitute arguments into begin definition
            subbed_begin = expander.substitute_token_args(captured_begin_def, args)

            # Create a temporary env def with the substituted begin definition
            # and no args (since we already parsed them)
            temp_env_def = env_def.copy()
            temp_env_def.begin_definition = subbed_begin
            temp_env_def.end_definition = expander.substitute_token_args(
                captured_end_def, args
            )
            temp_env_def.num_args = 0
            temp_env_def.default_arg = None

            return process_environment_begin(
                expander, token, env_name, temp_env_def
            )

        env_def = EnvironmentDefinition(
            name=env_name,
            begin_definition=begin_definition,
            end_definition=end_definition,
            num_args=0,  # We handle args in the custom handler
            default_arg=None,
            has_direct_command=env_name.isalpha(),
        )
        env_def.begin_handler = env_begin_handler

        expander.register_environment(
            env_name, env_def, is_global=True, is_user_defined=True
        )

        return []


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

    # Environment declarations
    expander.register_macro(
        "\\NewDocumentEnvironment",
        NewDocumentEnvironmentMacro("\\NewDocumentEnvironment", allow_redefine=False),
        is_global=True,
    )
    expander.register_macro(
        "\\RenewDocumentEnvironment",
        NewDocumentEnvironmentMacro("\\RenewDocumentEnvironment", allow_redefine=True),
        is_global=True,
    )
    expander.register_macro(
        "\\DeclareDocumentEnvironment",
        NewDocumentEnvironmentMacro(
            "\\DeclareDocumentEnvironment", allow_redefine=True
        ),
        is_global=True,
    )

    # Register IfBoolean conditionals
    register_ifboolean_commands(expander)

    # Register IfValue conditionals
    register_ifvalue_commands(expander)


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
