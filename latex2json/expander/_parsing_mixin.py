"""Mixin providing token parsing helpers for ExpanderCore."""

from __future__ import annotations

from typing import Any, Callable, List, Optional, Tuple, TYPE_CHECKING, Union

from latex2json.registers.defaults.boxes import BASE_BOXES
from latex2json.registers.types import Box
from latex2json.registers import RegisterType
from latex2json.expander.macro_registry import MacroType, RelaxMacro
from latex2json.expander.utils import (
    RELAX_TOKEN,
    integer_tok_cur_str_predicate,
    is_token_command_name,
    parse_number_str_to_float,
)
from latex2json.expander.state import ProcessingMode
from latex2json.registers.utils import dimension_to_scaled_points
from latex2json.tokens import Catcode, Token, TokenType
from latex2json.tokens.utils import (
    DelimiterDepthTracker,
    is_1_to_9_token,
    is_begin_bracket_token,
    is_begin_group_token,
    is_end_group_token,
    is_param_token,
    is_whitespace_token,
    strip_whitespace_tokens,
)

if TYPE_CHECKING:
    from latex2json.expander.expander_core import ExpanderCore

TokenPredicate = Callable[[Token], bool]


class ParsingMixin:
    """Token parsing helpers mixed into ExpanderCore."""

    # Annotate self for IDE support — at runtime this is ExpanderCore
    if TYPE_CHECKING:

        def peek(self) -> Optional[Token]: ...
        def consume(self) -> Optional[Token]: ...
        def eof(self) -> bool: ...
        def skip_whitespace(self) -> int: ...
        def match(self, **kwargs) -> bool: ...
        def is_control_sequence(self, tok: Token) -> bool: ...
        def parse_brace_as_tokens(self, expand: bool = False) -> Optional[List[Token]]: ...
        def parse_bracket_as_tokens(self, expand: bool = False) -> Optional[List[Token]]: ...
        def parse_parenthesis_as_tokens(self, expand: bool = False) -> Optional[List[Token]]: ...
        def check_tokens_equal(self, a: List[Token], b: List[Token]) -> bool: ...
        def convert_tokens_to_str(self, tokens: List[Token]) -> str: ...
        def convert_str_to_tokens(self, text: str, catcode: Optional[Catcode] = None) -> List[Token]: ...
        def get_macro(self, tok_or_name) -> Any: ...
        def push_tokens(self, tokens: List[Token]) -> None: ...
        def expand_next(self) -> Optional[List[Token]]: ...
        def expand_tokens(self, tokens: List[Token]) -> List[Token]: ...
        def get_register_value(self, rt: Any, ri: Any, rd: bool = False) -> Any: ...
        def _check_recursion(self, tok: Token) -> None: ...
        stream: Any
        state: Any
        logger: Any

    def skip_whitespace_not_eol(self):
        space_cnt = 0
        while not self.eof():
            tok = self.peek()
            if tok is None:
                break
            if tok.type == TokenType.CHARACTER and tok.catcode == Catcode.SPACE:
                self.consume()
                space_cnt += 1
            else:
                break
        return space_cnt

    def is_relax_token(self, token: Token) -> bool:
        if isinstance(self.get_macro(token), RelaxMacro):
            return True
        return False

    def _expand_and_combine_as_str(
        self,
        tok_cur_str_predicate: Callable[[Token, str], bool],
        expand_registers=False,
    ) -> Tuple[str, bool]:
        """
        Returns (str, bool) where str is the combined string and bool is whether relax was encountered
        """
        # Use list accumulator instead of string concat for O(n) instead of O(n²)
        parts: List[str] = []
        # Track current string for predicate (rebuilt only when needed)
        cur_str = ""

        last_exp = None
        while not self.eof():
            tok = self.peek()
            if tok:
                self._check_recursion(tok)

            if tok_cur_str_predicate(tok, cur_str):
                self.consume()
                parts.append(tok.value)
                cur_str += tok.value  # Update for predicate checks
            elif self.is_control_sequence(tok):
                # if we see a declaration macro e.g. \def or \newcommand, exit
                macro = self.get_macro(tok)
                if macro and macro.type == MacroType.DECLARATION:
                    return "".join(parts), False

                # check \relax token and that it is RelaxMacro i.e. has not been redefined
                if self.is_relax_token(tok):
                    self.consume()  # consume \relax token itself
                    return "".join(parts), True

                if self._is_next_token_register():
                    if expand_registers:
                        # parse register value literal i.e. without any expanding
                        reg_out = self.parse_register_value(expand=False)
                        if reg_out is not None:
                            self.push_tokens(self.convert_str_to_tokens(str(reg_out)))
                            tok = self.peek()
                            continue
                    else:
                        break

                # expand and continue loop
                exp = self.expand_next()
                if not exp:
                    continue

                # if expanded are not equal, push expanded tokens back onto stream
                if not self.check_tokens_equal(exp, [tok]):
                    self.push_tokens(exp)
                else:
                    # push original token back onto stream
                    self.push_tokens([tok])
                    break
                if last_exp == exp:
                    # inf recursion?
                    break
                last_exp = exp
            else:
                break
        return "".join(parts), False

    def _set_verbatim_mode_context(self, verbatim: bool):
        if verbatim:
            self.stream.set_verbatim_mode(True)

    def _reset_verbatim_mode_context(self, verbatim: bool):
        if verbatim:
            self.stream.set_verbatim_mode(False)

    def parse_token(self, verbatim=False) -> Optional[Token]:
        """Don't push mode here, since that should only be handled in expansion (and not parse phase)"""
        if verbatim:
            return self.consume()

        tok = self.peek()
        if tok is None:
            self.consume()
            if not self.eof():
                return self.parse_token(verbatim=verbatim)
            return None
        if is_param_token(tok):
            param = self.parse_parameter_token()
            if param:
                return param
        return self.consume()

    def parse_tokens_until(
        self, predicate: TokenPredicate, consume_predicate=False, verbatim=False
    ) -> List[Token]:
        out = []
        self._set_verbatim_mode_context(verbatim)
        try:
            while not self.eof():
                tok = self.parse_token(verbatim=verbatim)
                if tok is None:
                    break
                if predicate(tok):
                    if not consume_predicate:  # if don't consume, push back
                        self.push_tokens([tok])
                    break
                out.append(tok)
        finally:
            self._reset_verbatim_mode_context(verbatim)
        return out

    def parse_immediate_token(
        self, expand=False, skip_whitespace=False
    ) -> List[Token] | None:
        if skip_whitespace:
            self.skip_whitespace()

        tok = self.peek()
        if not tok:
            return None

        tokens = []
        if is_begin_group_token(tok):
            tokens = self.parse_brace_as_tokens()
        else:
            tokens = [self.consume()]
        if expand:
            return self.expand_tokens(tokens)
        return tokens

    def parse_integer(self, expand_registers=True) -> Optional[int]:
        sequence, relax = self._expand_and_combine_as_str(
            integer_tok_cur_str_predicate, expand_registers=expand_registers
        )
        if not sequence:
            return None

        parsed_float = parse_number_str_to_float(sequence.strip())
        if parsed_float is None:
            # pushback the sequence tokens on failed parse
            self.push_tokens(self.convert_str_to_tokens(sequence))
            return None
        return int(parsed_float)

    def parse_float(self, expand_registers=True) -> Optional[float]:
        parsed = self._parse_float(expand_registers=expand_registers)
        if parsed is None:
            return None
        return parsed[0]

    def _parse_float(self, expand_registers=True) -> Optional[Tuple[float, bool]]:
        def float_tok_cur_str_predicate(tok: Token, cur_str: str) -> bool:
            is_valid = integer_tok_cur_str_predicate(tok, cur_str)
            if is_valid:
                return True
            # float can only have one decimal point. Allow , for decimals
            if tok.value in ".,":
                if not ("." in cur_str or "," in cur_str):
                    return True
            return False

        sequence, relax = self._expand_and_combine_as_str(
            float_tok_cur_str_predicate, expand_registers=expand_registers
        )
        if not sequence:
            return None
        parsed_float = parse_number_str_to_float(sequence.strip())
        if parsed_float is None:
            # pushback the sequence tokens on failed parse
            self.push_tokens(self.convert_str_to_tokens(sequence))
            return None
        return parsed_float, relax

    def _is_next_token_register(self) -> bool:
        tok = self.peek()
        if tok is None:
            return False

        macro = self.get_macro(tok)
        if macro and macro.type == MacroType.REGISTER:
            return True
        return False

    def parse_register(
        self, expand=True
    ) -> Optional[Tuple[RegisterType, Union[int, str]]]:
        # won't work for boxes since they are different

        # Import here to avoid circular dependency with register handlers
        from latex2json.expander.handlers.registers.base_register_handlers import (
            RegisterMacro,
        )

        tok = self.peek()
        if tok is None:
            return None

        macro = self.get_macro(tok)
        if macro and isinstance(macro, RegisterMacro):
            return macro.parse_register(self, tok)

        if expand:
            # expand in case
            exp = self.expand_next()
            if exp:
                self.push_tokens(exp)
            self.skip_whitespace()
            tok = self.peek()
            if tok is None:
                return None
            out = None
            macro = self.get_macro(tok)
            if macro and isinstance(macro, RegisterMacro):
                out = macro.parse_register(self, tok)

            return out
        return None

    def parse_register_value(self, expand=True) -> Optional[Any]:
        tok = self.peek()
        if tok is None:
            return None
        out = self.parse_register(expand=expand)
        if out is None:
            return None
        return self.get_register_value(out[0], out[1])

    def parse_dimensions(self, parse_unknown=True) -> Optional[int]:
        """
        Parse dimensions from the token stream.

        Args:
            parse_unknown: If True, parse unknown control sequences that could be
                          unregistered or unhandled register macros in real-world LaTeX
                          (e.g., @someskip, custom dimension registers)
        """
        parsed = self._parse_dimensions(parse_unknown=parse_unknown)
        if parsed is None:
            return None
        return parsed[0]

    def _parse_dimensions(self, parse_unknown=True) -> Optional[Tuple[int, bool]]:
        """
        Cases: [optional multiplier float] dimen_register OR  dimension_float [space] dimension_unit

        Args:
            parse_unknown: If True, parse unknown control sequences that could be
                          unregistered or unhandled register macros in real-world LaTeX
                          (e.g., @someskip, custom dimension registers)

        Returns: (int, bool) where int is the parsed value and bool is whether relax
        """
        register_value = self.parse_register_value(expand=True)
        if register_value is not None:
            return register_value, False
        self.skip_whitespace()

        parsed_float = self._parse_float(expand_registers=False)
        if not parsed_float:
            if parse_unknown:
                # Parse unknown control sequences that could be unregistered or
                # unhandled register macros in real-world LaTeX (e.g., @someskip)
                next_tok = self.peek()
                if next_tok and self.is_control_sequence(next_tok):
                    if next_tok == RELAX_TOKEN:
                        self.consume()
                        relax = True
                        return 0, True

                    elif not self.get_macro(next_tok):
                        # Unknown control sequence - treat as 0 value register?
                        self.consume()
                        return 0, False
            return None
        digits, relax = parsed_float

        unit = None
        if not relax and self.peek():
            self.skip_whitespace()

            if self.is_relax_token(self.peek()):
                self.consume()
                relax = True
            else:
                register_value = self.parse_register_value(expand=True)
                if isinstance(register_value, float | int):
                    return int(register_value * digits), False

                # now parse for regular units. First check for true keyword
                if self.parse_keyword("true"):
                    self.skip_whitespace()

                unit, relax = self._expand_and_combine_as_str(
                    lambda tok, cur_str: (
                        tok.catcode == Catcode.LETTER and " " not in cur_str
                    )
                )

        pts = dimension_to_scaled_points(digits, unit)
        if pts is None and unit:
            # pushback the sequence tokens on failed parse
            self.push_tokens(self.convert_str_to_tokens(unit))
        return dimension_to_scaled_points(digits, unit), relax

    def parse_box(self) -> Optional[Box]:
        r"""
        \hbox{content}              % Just type + content
        \vbox to 5cm{content}       % Type + "to" + dimension + content
        \vtop spread 1cm{content}   % Type + "spread" + dimension + content
        """

        tok = self.peek()
        if tok is None or tok.type != TokenType.CONTROL_SEQUENCE:
            return None
        box_type = tok.value
        if box_type not in BASE_BOXES:
            self.logger.warning(f"Unknown box command: \\{box_type}")
            return None
        self.consume()
        self.skip_whitespace()

        tok = self.peek()
        if tok is None:
            return None

        operator = None
        if self.parse_keyword("to"):
            operator = "to"
        elif self.parse_keyword("spread"):
            operator = "spread"

        if operator:
            self.skip_whitespace()
            dims = self.parse_dimensions()
            self.skip_whitespace()

        # Parse brace content, recognizing both {/} and \bgroup/\egroup
        def is_begin_group_or_bgroup(tok: Token) -> bool:
            return is_begin_group_token(tok) or (
                tok.type == TokenType.CONTROL_SEQUENCE and tok.value == "bgroup"
            )

        def is_end_group_or_egroup(tok: Token) -> bool:
            return is_end_group_token(tok) or (
                tok.type == TokenType.CONTROL_SEQUENCE and tok.value == "egroup"
            )

        content = self.parse_begin_end_as_tokens(
            is_begin_group_or_bgroup, is_end_group_or_egroup
        )
        if content:
            is_math = self.is_math_mode
            # box is always in text mode
            if is_math:
                self.state.push_mode(ProcessingMode.TEXT)
            content = self.expand_tokens(content)
            if is_math:
                self.state.pop_mode()
        if content is None:
            self.logger.warning(f"Could not find {{...}} after \\{box_type}")
            return None

        return Box(type=box_type, content=content)

    def parse_skip(self) -> Optional[int]:
        parsed = self._parse_skip()
        if parsed is None:
            return None
        return parsed[0]

    def _parse_skip(self) -> Optional[Tuple[int, bool]]:
        """
        must be in this order:
        skip_value = base_component [plus_component] [minus_component]
        where [...] is optional

        base_component = dimension | skip_register | expression
        plus_component = "plus" (dimension | skip_register | fill_spec)
        minus_component = "minus" (dimension | skip_register)

        Returns: (int, bool) where int is the parsed value and bool is whether relax
        """
        self.skip_whitespace()
        tok = self.peek()
        if is_begin_group_token(tok):
            # e.g. \vskip{\fill} or \vskip{0pt plus 1fil}
            brace_tokens = self.parse_brace_as_tokens(expand=True)
            self.push_tokens(brace_tokens + [RELAX_TOKEN.copy()])

        # Parse base component (required)
        base_result = self._parse_dimensions()
        if base_result is None:
            return None

        base_scaled_points, relax = base_result
        if relax:
            return base_scaled_points, True

        # Parse optional plus component
        self.skip_whitespace()
        tok = self.peek()
        is_at_plus_token = tok and is_token_command_name(tok, "@plus")
        if (
            is_at_plus_token
            or self.parse_keyword("plus")
            or self.parse_keyword("@plus")
        ):
            if is_at_plus_token:
                self.consume()
            self.skip_whitespace()
            plus_result = self._parse_dimensions()
            if plus_result:
                plus_scaled_points, relax = plus_result
                try:
                    base_scaled_points += plus_scaled_points
                except TypeError:
                    pass  # Skip if values are None
                if relax:
                    return base_scaled_points, True

        # Parse optional minus component
        self.skip_whitespace()
        tok = self.peek()
        if not tok:
            return base_scaled_points, False
        if self.is_relax_token(tok):
            self.consume()
            return base_scaled_points, True

        is_at_minus_token = tok and is_token_command_name(tok, "@minus")
        if (
            is_at_minus_token
            or self.parse_keyword("minus")
            or self.parse_keyword("@minus")
        ):
            if is_at_minus_token:
                self.consume()
            self.skip_whitespace()
            minus_result = self._parse_dimensions()
            if minus_result:
                minus_scaled_points, relax = minus_result
                try:
                    base_scaled_points -= minus_scaled_points
                except TypeError:
                    pass  # Skip if values are None
                if relax:
                    return base_scaled_points, True

        return base_scaled_points, False  # Return the base dimension and no relax

    def parse_keyword(self, keyword: str) -> bool:
        return self.parse_keyword_sequence([keyword], skip_whitespaces=False)

    # includes \control sequences
    # e.g. self.parse_keyword_sequence([",", r"\@nil", r"\@@"], skip_whitespaces=True)
    def parse_keyword_sequence(
        self, keywords: List[str], skip_whitespaces=True
    ) -> bool:
        consumed_tokens: List[Token] = []

        rt = True
        for word in keywords:
            if skip_whitespaces:
                self.skip_whitespace()
            tok = self.peek()
            if tok is None:
                rt = False
                break
            elif word.startswith("\\"):
                if tok.type != TokenType.CONTROL_SEQUENCE or tok.value != word[1:]:
                    rt = False
                    break
                self.consume()
                consumed_tokens.append(tok)
            else:
                # check character by character
                for c in word:
                    tok = self.consume()
                    consumed_tokens.append(tok)
                    if c == " " and is_whitespace_token(tok):
                        continue
                    if (
                        tok is None
                        or tok.value != c
                        or tok.type == TokenType.CONTROL_SEQUENCE
                    ):
                        rt = False
                        break
            if not rt:
                break
        if not rt:
            self.push_tokens(consumed_tokens)
        return rt

    def parse_equals(self) -> bool:
        if self.match(value="=", catcode=Catcode.OTHER):
            self.consume()
            return True
        return False

    def parse_angle_brackets(self) -> str:
        if self.match(value="<", catcode=Catcode.OTHER) or self.match(
            value=">", catcode=Catcode.OTHER
        ):
            return self.consume().value
        return None

    def parse_asterisk(self) -> bool:
        if self.match(value="*", catcode=Catcode.OTHER):
            self.consume()
            return True
        return False

    # simulate Tex engine behavior of parsing #1 -> Parameter token '1', ##1 -> "#", 1
    def parse_parameter_token(self) -> Optional[Token]:
        """
        Parses a TeX parameter sequence (#N) or an escaped hash (##) from the stream,
        as encountered when parsing a macro definition body.

        This function assumes the current token being peeked at is a
        '#' character with Catcode.PARAMETER.

        Returns:
            A single Token representing the parsed parameter (#N) or literal hash (#),
            or None if there's a syntax error (e.g., # followed by non-digit/non-#).
        """
        # Ensure we are starting with a '#' token with Catcode.PARAMETER
        # This check is defensive, as the caller should ensure this.
        tok = self.peek()
        if not tok:
            return None
        if not is_param_token(tok):
            self.logger.warning(
                f"parse_parameter_sequence called without current Catcode.PARAMETER: {tok}"
            )
            return None  # Not the start of a parameter sequence

        # Consume the initial '#' token
        self.consume()

        # Peek the token immediately following the first '#'
        tok = self.peek()

        if tok is None:
            self.logger.error(
                "Unexpected end of input after '#'. Expected a digit (1-9) or another '#'."
            )
            return None  # Syntax error: incomplete sequence

        # Case 1: ## -> Literal '#'
        if is_param_token(tok):
            self.consume()  # Consume the second '#'
            return tok  # return as literal #

        # Case 2: #N -> Parameter token (N must be 1-9)
        if is_1_to_9_token(tok):  # Check for digits '1' through '9'
            self.consume()  # Consume the digit
            return Token(TokenType.PARAMETER, tok.value)

        # Case 3: # followed by something else (error in definition)
        self.logger.info(f"Illegal token: {tok} after '#'. Skipping.")
        return None  # Indicate an error for the parser to handle

    def parse_begin_end_as_tokens(
        self,
        begin_predicate: TokenPredicate,
        end_predicate: TokenPredicate,
        check_first_token: bool = True,
        verbatim: bool = False,
    ) -> Optional[List[Token]]:
        """
        Parses a sequence of tokens enclosed in braces '{...}' and returns them as a List[Token].
        The outermost braces are NOT included in the returned list.
        Handles nested braces correctly.

        check_first_token = False is useful if the first token is already consumed and we want to move on
        """
        # 1. Peek at the very first token to check for the opening brace
        first_token = self.peek()

        if not first_token:
            return None

        if check_first_token:
            if not begin_predicate(first_token):
                return None
            self.consume()

        self._set_verbatim_mode_context(verbatim)
        try:
            out_tokens: List[Token] = []
            tracker = DelimiterDepthTracker(begin_predicate)

            while tracker.is_open:
                current_token = self.peek()

                if current_token is None:
                    self.logger.info(
                        "Expander - Unmatched braces: Reached end of stream within a definition."
                    )
                    break

                tracker.update(current_token, begin_predicate, end_predicate)
                current_token = self.parse_token(verbatim=verbatim)

                if tracker.is_open:
                    out_tokens.append(current_token)

            return out_tokens
        finally:
            self._reset_verbatim_mode_context(verbatim)

    def convert_token_to_char_token(self, token: Token) -> Optional[Token]:
        macro = self.get_macro(token)
        if macro:
            if macro.type == MacroType.CHAR and len(macro.definition) > 0:
                # example \let\a=3, \bgroup -> {, \egroup -> }, etc
                return macro.definition[0]
            return None
        return token

    # converts a list of tokens into their associated macro definitions if exists
    def convert_to_macro_definitions(self, definition: List[Token]) -> List[Token]:
        final_definition = []
        for tok in definition:
            macro = self.get_macro(tok)
            if macro:
                final_definition.extend(macro.definition)
                continue
            final_definition.append(tok)
        return final_definition

    def parse_command_name_token(self) -> Optional[Token]:
        self.skip_whitespace()

        # Parse command name
        cmd = self.parse_immediate_token(expand=False)
        cmd = strip_whitespace_tokens(cmd)
        if not cmd:
            return None
        cmd = cmd[0]
        if self.is_control_sequence(cmd):
            return cmd
        return None

    def parse_brace_name(self, bracket=False) -> Optional[str]:
        self.skip_whitespace()

        tok = self.peek()
        if not tok:
            return None

        tokens = (
            self.parse_brace_as_tokens(expand=True)
            if not bracket
            else self.parse_bracket_as_tokens(expand=True)
        )
        # don't strip, env names are literal
        if tokens is not None:
            return self.convert_tokens_to_str(tokens)

        return None

    def get_parsed_args(
        self,
        num_args: int,
        default_arg: Optional[List[Token]] = None,
        force_braces_for_req_args=False,
        command_name: Optional[str] = None,
    ) -> List[List[Token]]:
        if num_args > 0:
            # e.g. \cmd {arg}
            self.skip_whitespace()
        args: List[List[Token]] = []

        if default_arg is not None:
            tok = self.peek()
            # if the next token is a begin bracket, replace the default arg with the parsed bracket
            if tok and is_begin_bracket_token(tok):
                default_arg = self.parse_bracket_as_tokens()

            args.append(default_arg.copy())
            num_args -= 1

        for i in range(num_args):
            self.skip_whitespace()
            if force_braces_for_req_args:
                tokens = self.parse_brace_as_tokens()
            else:
                tokens = self.parse_immediate_token()
            if tokens is None:
                self.logger.info(
                    f"{command_name} expected argument {i+1} but found nothing"
                )
                return args
            elif tokens and is_end_group_token(tokens[0]):
                self.logger.warning(
                    f"{command_name} expected argument {i+1}"
                    + " but found early closing brace }"
                )
                # push tokens back to stream, since this is invalid
                self.push_tokens(tokens)
                return None
            args.append(tokens)

        return args

    def parse_braced_blocks(
        self, N_blocks: int = 2, expand=False, check_immediate_tokens=False
    ) -> List[List[Token]]:
        blocks = []
        for _ in range(N_blocks):
            self.skip_whitespace()
            block = (
                self.parse_brace_as_tokens(expand=expand)
                if not check_immediate_tokens
                else self.parse_immediate_token(expand=expand)
            )
            if block is None:
                break
            blocks.append(block)

        return blocks

    def parse_bracket_blocks(
        self, N_blocks: int = 2, expand=False
    ) -> List[List[Token]]:
        blocks = []
        for _ in range(N_blocks):
            self.skip_whitespace()
            block = self.parse_bracket_as_tokens(expand=expand)
            if block is None:
                break
            blocks.append(block)

        return blocks
