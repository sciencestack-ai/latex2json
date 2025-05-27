from logging import Logger
from typing import Callable, List, Any, Dict, Optional, Tuple, Type, Union


from latex2json.tokens.types import (
    BEGIN_BRACE_TOKEN,
    END_BRACE_TOKEN,
    EnvironmentStartToken,
)
from latex2json.tokens.utils import (
    is_mathshift_token,
    substitute_token_args,
    wrap_tokens_in_braces,
)
from latex2json.expander.macro_registry import (
    Handler,
    Macro,
    MacroRegistry,
    MacroType,
)

from latex2json.latex_maps.environments import EnvironmentDefinition
from latex2json.registers import (
    RegisterType,
    TexRegisters,
)

from latex2json.expander.state import ExpanderState, ProcessingMode
from latex2json.expander.utils import parse_number_str_to_float
from latex2json.latex_maps.dimensions import dimension_to_scaled_points
from latex2json.tokens import Catcode, Token, TokenType, Tokenizer
from latex2json.tokens.token_stream import (
    TokenStream,
)
from latex2json.tokens.utils import (
    is_1_to_9_token,
    is_begin_bracket_token,
    is_begin_group_token,
    is_end_bracket_token,
    is_end_group_token,
    is_signed_integer_token,
    is_digit_token,
    is_param_token,
    is_whitespace_token,
)

# arbitrary character that is not a valid token
RELAX_TOKEN = Token(TokenType.CONTROL_SEQUENCE, "relax")

TokenPredicate = Callable[[Token], bool]


def is_relax_token(token: Token) -> bool:
    return token.type == TokenType.CONTROL_SEQUENCE and token.value == "relax"


class EmptyMacro(Macro):
    def __init__(self):
        super().__init__("empty", lambda expander, token: [], definition=[])


class RelaxMacro(Macro):
    def __init__(self):
        super().__init__(
            "relax",
            lambda expander, token: [token],  # return the \relax token itself
            definition=[RELAX_TOKEN.copy()],
        )


def make_the_counter_handler(counter_name: str):
    def the_counter_handler(expander: "ExpanderCore", token: Token):
        value = expander.state.get_counter_as_format(counter_name)
        if value is None:
            return None
        return expander.convert_str_to_tokens(str(value))

    return the_counter_handler


class ExpanderCore:
    """
    The main engine for processing the document.
    Drives parsing, manages state, executes commands, and performs expansion.
    """

    def __init__(
        self,
        tokenizer: Optional[Tokenizer] = None,
        logger: Optional[Logger] = None,
    ):
        """Initialize the expander core.

        Args:
            tokenizer: Optional tokenizer instance. If None, creates a new one with fresh catcodes.
            logger: Logger instance for debugging.
        """
        self.tokenizer = tokenizer if tokenizer is not None else Tokenizer()
        self.stream = TokenStream(self.tokenizer)
        self.state = ExpanderState(self.tokenizer)
        self.logger = logger if logger is not None else Logger("expander")

        self._init_macros()

    @property
    def macros(self) -> MacroRegistry:
        return self.state.current.macro_registry

    def _init_macros(self):
        self._init_state_macros()
        self._init_counter_macros()
        self._init_math_macros()

        def newline_handler(expander: "ExpanderCore", token: Token):
            return [Token(TokenType.END_OF_LINE, "\n\n")]

        self.register_handler("\\newline", newline_handler, is_global=True)

    def _init_math_macros(self):
        def make_begin_end_math_handlers(mode: ProcessingMode):
            out_token = Token(TokenType.MATH_SHIFT_INLINE, "$")
            if mode == ProcessingMode.MATH_DISPLAY:
                out_token = Token(TokenType.MATH_SHIFT_DISPLAY, "$$")

            def begin_math_handler(expander: "ExpanderCore", token: Token):
                expander.state.push_mode(mode)
                return [out_token.copy()]

            def end_math_handler(expander: "ExpanderCore", token: Token):
                if expander.state.is_math_mode:
                    expander.state.pop_mode()
                return [out_token.copy()]

            return begin_math_handler, end_math_handler

        inline_begin, inline_end = make_begin_end_math_handlers(
            ProcessingMode.MATH_INLINE
        )
        display_begin, display_end = make_begin_end_math_handlers(
            ProcessingMode.MATH_DISPLAY
        )

        self.register_handler("\\(", inline_begin, is_global=True)
        self.register_handler("\\)", inline_end, is_global=True)

        self.register_handler("\\[", display_begin, is_global=True)
        self.register_handler("\\]", display_end, is_global=True)

    def _init_state_macros(self):
        def global_handler(expander: "ExpanderCore", token: Token):
            expander.state.pending_global = True
            return []

        self.register_handler("\\global", global_handler, is_global=True)
        self.register_macro("\\empty", EmptyMacro(), is_global=True)
        self.register_macro("\\relax", RelaxMacro(), is_global=True)

    def _init_counter_macros(self):
        for counter_name in self.state.counter_manager.counters:
            self.register_handler(
                f"\\the{counter_name}",
                make_the_counter_handler(counter_name),
                is_global=True,
            )

    # counters
    def create_new_counter(self, counter_name: str, parent: Optional[str] = None):
        self.state.new_counter(counter_name, parent)
        self.register_handler(
            f"\\the{counter_name}",
            make_the_counter_handler(counter_name),
            is_global=True,
        )

    # MACROS
    def get_macro(self, name: str) -> Optional[Macro]:
        return self.state.get_macro(name)

    def get_all_macros(self) -> Dict[str, Macro]:
        return self.state.get_all_macros()

    def register_macro(self, name: str, macro: Macro, is_global: bool = False):
        self.state.set_macro(name, macro, is_global=is_global)

    def register_handler(self, name: str, handler: Handler, is_global: bool = False):
        macro = Macro(name, handler)
        self.state.set_macro(name, macro, is_global=is_global)

    def substitute_token_args(
        self, tokens: List[Token], args: List[List[Token]]
    ) -> List[Token]:
        is_math = self.state.is_math_mode
        if is_math:
            for i, arg in enumerate(args):
                args[i] = wrap_tokens_in_braces(arg)
        out = substitute_token_args([t.copy() for t in tokens], args)
        if is_math and out:
            has_trailing_character = False
            if (
                out[0].type == TokenType.CHARACTER
                or out[-1].type == TokenType.CHARACTER
            ):
                has_trailing_character = True
            if has_trailing_character:
                out = wrap_tokens_in_braces(out)
        return out

    # REGISTERS
    @property
    def registers(self) -> TexRegisters:
        return self.state.registers

    def get_register_value(
        self,
        register_type: RegisterType,
        reg_id: Union[int, str],
        return_default=False,
    ) -> Optional[Any]:
        return self.state.get_register(register_type, reg_id, return_default)

    def get_register_value_as_tokens(
        self,
        register_type: RegisterType,
        reg_id: Union[int, str],
        return_default=False,
    ) -> Optional[List[Token]]:
        value = self.get_register_value(register_type, reg_id, return_default)
        if value is None:
            return None
        return self.convert_str_to_tokens(str(value))

    def set_register(
        self,
        register_type: RegisterType,
        reg_id: Union[int, str],
        value: Any,
        is_global: bool = False,
    ):
        self.state.set_register(register_type, reg_id, value, is_global=is_global)

    def increment_register(
        self,
        register_type: RegisterType,
        reg_id: Union[int, str],
        increment: Any,
    ):
        self.state.increment_register(register_type, reg_id, increment)

    # PROCESSING
    def set_text(self, text: str):
        self.stream.set_text(text)

    def eof(self) -> bool:
        return self.stream.eof()

    def expand(self, text: str) -> List[Token]:
        self.set_text(text)
        return self.process()

    def expand_tokens(self, tokens: List[Token]) -> List[Token]:
        STOP_TOKEN = Token(TokenType.CHARACTER, r"\0", catcode=Catcode.OTHER)
        self.push_tokens(tokens + [STOP_TOKEN])
        out = self.process(
            stop_token_logic=lambda tok: tok is STOP_TOKEN, consume_stop_token=True
        )
        return out

    def process(
        self,
        stop_token_logic: Optional[TokenPredicate] = None,
        consume_stop_token: bool = True,
    ) -> List[Token]:
        """
        Processes the entire token stream, performing expansions and executing side effects,
        until the stop token is encountered.
        """
        final_expanded_tokens: List[Token] = []

        while not self.eof():
            current_token = self.peek()  # Peek at the next token

            if current_token is None:  # Should be caught by eof(), but defensive check
                break
            if stop_token_logic and stop_token_logic(current_token):
                if consume_stop_token:
                    self.consume()
                break

            processed = self.expand_next()
            if processed:
                final_expanded_tokens.extend(processed)

        return final_expanded_tokens

    def push_scope(self):
        self.state.push_scope()

    def pop_scope(self):
        self.state.pop_scope()

    def push_tokens(self, tokens: List[Token]):
        self.stream.push_tokens(tokens)

    def peek(self, offset: int = 0) -> Optional[Token]:
        return self.stream.peek(offset)

    def consume(self) -> Optional[Token]:
        return self.stream.consume()

    def skip_whitespace(self):
        return self.stream.skip_whitespace()

    # main parsing logic
    def expand_next(self) -> Optional[List[Token]]:
        tok = self.parse_token()
        if tok is None:
            return None

        if tok.type == TokenType.CONTROL_SEQUENCE:
            macro = self.state.get_macro(tok.value)
            if macro and macro.handler:
                processed = macro.handler(self, tok)
                return processed
        else:
            self.state.pending_global = False
            if is_begin_group_token(tok):
                self.push_scope()
            elif is_end_group_token(tok):
                self.pop_scope()
            elif is_mathshift_token(tok):
                mode_type = (
                    ProcessingMode.MATH_INLINE
                    if tok.type == TokenType.MATH_SHIFT_INLINE
                    else ProcessingMode.MATH_DISPLAY
                )
                self.state.toggle_math_mode(mode_type)
        return [tok]

    def next_non_expandable_tokens(self) -> Optional[List[Token]]:
        while not self.eof():
            out = self.expand_next()
            if out and len(out) > 0:
                return out
        return None

    def parse_token(self) -> Optional[Token]:
        tok = self.peek()
        if tok is None:
            return None
        if is_param_token(tok):
            param = self.parse_parameter_token()
            if param:
                return param
        return self.consume()

    def parse_tokens_until(self, predicate: TokenPredicate) -> Optional[List[Token]]:
        out = []
        while not self.eof():
            tok = self.parse_token()
            if predicate(tok):
                self.push_tokens([tok])
                break
            out.append(tok)
        return out

    # parser helper functions
    def match(
        self,
        token_type: Optional[TokenType] = None,
        value: Optional[str] = None,
        catcode: Optional[Catcode] = None,
    ) -> bool:
        return self.stream.match(token_type, value, catcode)

    def _expand_and_combine_as_str(
        self,
        predicate: Callable[[Token], bool],
        expand_registers=False,
        skip_whitespace=True,
    ) -> Tuple[str, bool]:
        tok = self.peek()
        out = ""

        while tok:
            if predicate(tok):
                self.consume()
                out += tok.value
            elif skip_whitespace and is_whitespace_token(tok) and len(out) == 0:
                # if whitespace and no output yet, consume and continue
                self.consume()
                tok = self.peek()
                continue
            elif tok.type == TokenType.CONTROL_SEQUENCE:
                # check \relax token and that it is RelaxMacro i.e. has not been redefined
                if is_relax_token(tok) and isinstance(
                    self.get_macro(tok.value), RelaxMacro
                ):
                    self.consume()  # consume \relax token itself
                    return out, True

                if expand_registers:
                    # parse register value literal i.e. without any expanding
                    reg_out = self.parse_register_value(expand=False)
                    if reg_out is not None:
                        self.push_tokens(self.convert_str_to_tokens(str(reg_out)))
                        tok = self.peek()
                        continue

                # expand and continue loop
                exp = self.expand_next()
                # if expanded are not equal, push expanded tokens back onto stream
                if not self.check_tokens_equal(exp, [tok]):
                    self.push_tokens(exp)
                else:
                    # push original token back onto stream
                    self.push_tokens([tok])
                    break
            else:
                break
            tok = self.peek()
        return out, False

    def parse_immediate_token(self) -> List[Token] | None:
        tok = self.peek()
        if not tok:
            return None

        if is_begin_group_token(tok):
            return self.parse_brace_as_tokens()
        return [self.consume()]

    def parse_integer(self) -> Optional[int]:
        sequence, relax = self._expand_and_combine_as_str(
            is_signed_integer_token, expand_registers=True
        )
        if not sequence:
            return None
        return int(parse_number_str_to_float(sequence))

    def parse_float(self) -> Optional[float]:
        sequence, relax = self._expand_and_combine_as_str(
            is_digit_token, expand_registers=True
        )
        if not sequence:
            return None
        return parse_number_str_to_float(sequence)

    def parse_register(
        self, expand=True
    ) -> Optional[Tuple[RegisterType, Union[int, str]]]:

        # Import here to avoid circular dependency with register handlers
        from latex2json.expander.handlers.registers.base_register_handlers import (
            get_register_handler,
        )

        tok = self.peek()
        if tok is None or tok.type != TokenType.CONTROL_SEQUENCE:
            return None

        macro = self.get_macro(tok.value)
        if macro and macro.type == MacroType.REGISTER:
            return get_register_handler(self, tok)

        if expand:
            # expand in case
            exp = self.expand_next()
            self.push_tokens(exp)
            start_pos = self.skip_whitespace()
            tok = self.peek()
            if tok is None:
                return None
            out = get_register_handler(self, tok)
            if out is None:
                self.stream.set_pos(*start_pos)
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

    def parse_dimensions(self) -> Optional[int]:
        """
        Parses a sequence of digits followed by an optional unit.
        Returns a tuple (float, str) where the float is the number and the str is the unit.
        e.g. 15 pt
        """
        register_value = self.parse_register_value(expand=True)
        if register_value is not None:
            return register_value

        digits, relax = self._expand_and_combine_as_str(is_digit_token)
        if not digits:
            return None
        digits = float(digits)

        unit = None
        if not relax:
            self.skip_whitespace()

            if is_relax_token(self.peek()):
                self.consume()
            else:
                unit, relax = self._expand_and_combine_as_str(
                    lambda tok: tok.catcode == Catcode.LETTER
                )
        return dimension_to_scaled_points(digits, unit)

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
                f"WARNING: parse_parameter_sequence called without current Catcode.PARAMETER: {tok}"
            )
            return None  # Not the start of a parameter sequence

        # Consume the initial '#' token
        self.consume()

        # Peek the token immediately following the first '#'
        tok = self.peek()

        if tok is None:
            self.logger.error(
                "Error: Unexpected end of input after '#'. Expected a digit (1-9) or another '#'."
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
        self.logger.error(
            f"Error: Illegal parameter number or escape sequence after '#'. "
            f"Found '{tok})."
        )
        return None  # Indicate an error for the parser to handle

    def parse_begin_end_as_tokens(
        self,
        begin_predicate: TokenPredicate,
        end_predicate: TokenPredicate,
        check_first_token: bool = True,
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

        out_tokens: List[Token] = []
        brace_depth = 1  # We've consumed one opening brace, so depth starts at 1

        # 3. Loop until the matching closing brace is found (brace_depth returns to 0)
        while brace_depth > 0:
            current_token = self.peek()

            if current_token is None:
                # Error: Reached the end of the input stream before finding a matching closing brace.
                self.logger.warning(
                    "Unmatched braces: Reached end of stream within a definition."
                )
                # Depending on your error handling strategy, you might raise an exception here
                # or return the partially collected tokens.
                break  # Exit loop due to error

            # Check token type and update brace_depth
            if begin_predicate(current_token):
                brace_depth += 1
            elif end_predicate(current_token):
                brace_depth -= 1

            current_token = self.parse_token()

            if brace_depth > 0:
                out_tokens.append(current_token)

        return out_tokens

    def parse_brace_as_tokens(self) -> Optional[List[Token]]:
        return self.parse_begin_end_as_tokens(is_begin_group_token, is_end_group_token)

    def parse_bracket_as_tokens(self) -> Optional[List[Token]]:
        return self.parse_begin_end_as_tokens(
            is_begin_bracket_token, is_end_bracket_token
        )

    def set_catcode(self, char_ord: int, catcode: Catcode):
        self.state.set_catcode(char_ord, catcode)

    def get_catcode(self, char_ord: int) -> Catcode:
        return self.state.get_catcode(char_ord)

    def convert_token_to_char_token(self, token: Token) -> Optional[Token]:
        if token.type == TokenType.CONTROL_SEQUENCE:
            macro = self.get_macro(token.value)
            if macro and macro.type == MacroType.CHAR and len(macro.definition) > 0:
                # example \let\a=3, \bgroup -> {, \egroup -> }, etc
                return macro.definition[0]
            return None
        return token

    # converts a list of tokens into their associated macro definitions if exists
    def convert_to_macro_definitions(self, definition: List[Token]) -> List[Token]:
        final_definition = []
        for tok in definition:
            if tok.type == TokenType.CONTROL_SEQUENCE:
                macro = self.state.get_macro(tok.value)
                if macro:
                    final_definition.extend(macro.definition)
                    continue
            final_definition.append(tok)
        return final_definition

    def parse_environment_name(self) -> Optional[str]:
        self.skip_whitespace()

        tok = self.peek()
        if not tok or not is_begin_group_token(tok):
            return None

        name = self.parse_brace_as_tokens()
        expanded_name = self.expand_tokens(name)
        out_name = self.convert_tokens_to_str(
            expanded_name
        )  # don't strip, env names are literal

        return out_name

    def convert_str_to_tokens(self, text: str) -> List[Token]:
        out = []
        for c in text:
            catcode = self.get_catcode(ord(c))
            out.append(Token(TokenType.CHARACTER, c, catcode=catcode))
        return out

    @staticmethod
    def convert_tokens_to_str(tokens: List[Token]) -> str:
        return "".join(t.to_str() for t in tokens)

    @staticmethod
    def check_tokens_equal(a: List[Token], b: List[Token]) -> bool:
        if len(a) != len(b):
            return False
        for a_tok, b_tok in zip(a, b):
            if a_tok != b_tok:
                return False
        return True

    def get_parsed_args(
        self,
        num_args: int,
        default_arg: Optional[List[Token]] = None,
        force_braces_for_req_args=False,
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
                self.logger.warning(
                    f"Warning: expected argument {i+1} but found nothing"
                )
                return None
            args.append(tokens)

        return args

    def register_environment(
        self,
        env_def: EnvironmentDefinition,
        is_global: bool = True,
    ) -> None:
        """Register a new environment with begin/end handlers."""
        env_name = env_def.name
        self.state.set_environment_definition(env_name, env_def)

        is_math = env_def.is_math
        counter_name = env_def.counter_name
        if counter_name:
            self.state.new_counter(counter_name)

        def begin_handler(
            expander: "ExpanderCore", token: Token
        ) -> Optional[List[Token]]:
            state = expander.state
            if counter_name:
                state.step_counter(counter_name)

            state.push_env_stack(env_name)

            if is_math:
                state.push_mode(ProcessingMode.MATH_DISPLAY)

            args = expander.get_parsed_args(
                env_def.num_args, env_def.default_arg, force_braces_for_req_args=True
            )

            subbed = []
            if args is not None:
                subbed = expander.substitute_token_args(env_def.begin_definition, args)
                subbed = expander.expand_tokens(subbed)

            # evaluate the counter post begin definition expansion
            # e.g. some newenvironment definitions place \refstepcounter in the begin definition
            numbering = None
            if counter_name:
                numbering = state.get_counter_as_format(counter_name)
            begin_token = EnvironmentStartToken(
                env_name, numbering=numbering, is_math_env=is_math
            )
            return [begin_token] + subbed

        def end_handler(
            expander: "ExpanderCore", token: Token
        ) -> Optional[List[Token]]:
            end_token = Token(TokenType.ENVIRONMENT_END, env_name)

            expander.state.pop_env_stack()

            if is_math:
                expander.state.pop_mode()

            subbed = expander.substitute_token_args(env_def.end_definition, [])
            subbed = expander.expand_tokens(subbed)
            return subbed + [end_token]

        # attach the handlers to the envdef instance
        env_def.begin_handler = begin_handler
        env_def.end_handler = end_handler

        if env_def.has_direct_command and env_name.isalpha():
            self.register_macro(
                env_name,
                Macro(env_name, begin_handler, env_def.begin_definition),
                is_global=is_global,
            )
            self.register_macro(
                "end" + env_name,
                Macro("end" + env_name, end_handler, env_def.end_definition),
                is_global=is_global,
            )

    def parse_braced_blocks(self, N_blocks: int = 2) -> List[List[Token]]:
        blocks = []
        for _ in range(N_blocks):
            self.skip_whitespace()
            block = self.parse_brace_as_tokens()
            if block is None:
                break
            blocks.append(block)

        return blocks


if __name__ == "__main__":

    expander = ExpanderCore()

    # expander.set_text(r"$$")
    out = expander.expand(r"\[1_1\$$$$$2^2\]_")
