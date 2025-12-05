from dataclasses import dataclass
from logging import Logger
import os
from typing import Callable, List, Any, Dict, Optional, Set, Tuple, Type, Union


from latex2json.registers.defaults.boxes import BASE_BOXES
from latex2json.utils.encoding import read_file
from latex2json.registers.types import Box
from latex2json.tokens.catcodes import MATHMODE_CATCODES
from latex2json.tokens.types import BEGIN_ENV_TOKEN, END_ENV_TOKEN, CommandWithArgsToken
from latex2json.tokens.utils import (
    convert_str_to_tokens,
    is_begin_parenthesis_token,
    is_end_parenthesis_token,
    is_mathshift_token,
    is_whitespace_token,
    strip_whitespace_tokens,
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
from latex2json.registers.utils import dimension_to_scaled_points
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
    is_param_token,
)
from latex2json.utils.tex_utils import strip_latex_comments
from latex2json.utils.tex_versions import is_supported_tex_version

RELAX_TOKEN = Token(TokenType.CONTROL_SEQUENCE, "relax")

TokenPredicate = Callable[[Token], bool]


@dataclass
class EnvStackEntry:
    """Entry in the environment stack tracking nested environments."""

    env_name: str  # The environment name (e.g., "figure", "table")
    opening_token: (
        Token  # The token that opened this environment (\begin, \@float, etc.)
    )


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


def make_the_counter_macro(counter_name: str, formatted=True):
    def the_counter_handler(expander: "ExpanderCore", token: Token):
        value = (
            expander.state.get_counter_display(counter_name)
            if formatted
            else expander.state.get_counter_value(counter_name)
        )
        if value is None:
            return None
        return expander.convert_str_to_tokens(f"{value}")

    return Macro(f"the{counter_name}", the_counter_handler)


def integer_tok_cur_str_predicate(tok: Token, cur_str: str) -> bool:
    if tok.value.isdigit() or tok.value in "ABCDEF":
        return True
    has_digit = any(c.isdigit() or c in "ABCDEF" for c in cur_str)
    # allows for hex + octal + ascii + sign
    if not has_digit and tok.value in ["+", "-", " ", "'", '"', "`"]:
        return True
    return False


def is_token_command_name(tok: Token, command_name: str) -> bool:
    return tok.type == TokenType.CONTROL_SEQUENCE and tok.value == command_name


class ExpanderCore:
    """
    The main engine for processing the document.
    Drives parsing, manages state, executes commands, and performs expansion.
    """

    # Valid LaTeX file extensions
    VALID_LATEX_EXTENSIONS = {".tex", ".sty", ".cls", ".ltx", ".dtx"}

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
        self.logger = logger if logger is not None else Logger("expander")
        self.tokenizer = tokenizer if tokenizer is not None else Tokenizer()
        self.stream = TokenStream(self.tokenizer)
        self.state = ExpanderState(self.tokenizer, logger=self.logger)

        self.cwd = "."
        self.loaded_packages: Set[str] = set()
        self.loaded_classes: Set[str] = set()

        # Environment stack for tracking nested environments
        self._env_stack: List[EnvStackEntry] = []

        self._init_macros()

    @property
    def macros(self) -> MacroRegistry:
        return self.state.current.macro_registry

    @property
    def is_math_mode(self) -> bool:
        return self.state.is_math_mode

    @property
    def current_env(self) -> Optional[str]:
        return self._env_stack[-1].env_name if self._env_stack else None

    def get_env_stack(self) -> List[str]:
        """Returns a list of environment names currently on the stack."""
        return [entry.env_name for entry in self._env_stack]

    def push_env_stack(self, env_name: str, opening_token: Token):
        """Push an environment onto the stack with its opening token."""
        entry = EnvStackEntry(env_name=env_name, opening_token=opening_token)
        self._env_stack.append(entry)

    def find_env_entry(
        self, opening_cmd: str, most_recent: bool = True
    ) -> Optional[EnvStackEntry]:
        """
        Find the most recent env entry with matching opening command.

        Args:
            opening_cmd: The opening command value to search for (e.g., "begin", "@float", "@dblfloat")
            reverse: If True, search from most recent (default). If False, search from oldest.

        Returns:
            The matching EnvStackEntry, or None if not found
        """
        stack_iter = reversed(self._env_stack) if most_recent else iter(self._env_stack)
        for entry in stack_iter:
            if entry.opening_token.value == opening_cmd:
                return entry
        return None

    def pop_env_stack(
        self, target: Optional[Union[str, EnvStackEntry]] = None
    ) -> Optional[str]:
        """
        Pop an environment from the stack.

        Args:
            target: Can be:
                - None: pop the topmost entry
                - str: pop by env_name (backward search)
                - EnvStackEntry: pop that exact entry (by identity)

        Returns:
            The popped environment name, or None if stack is empty
        """
        if not self._env_stack:
            return None

        if target is None:
            entry = self._env_stack.pop()
            return entry.env_name

        if isinstance(target, str):
            # Find by env_name (existing behavior)
            for i in range(len(self._env_stack) - 1, -1, -1):
                if self._env_stack[i].env_name == target:
                    # Pop all environments from this point to the end
                    popped = self._env_stack[i:]
                    self._env_stack = self._env_stack[:i]
                    return popped[-1].env_name if popped else None

        elif isinstance(target, EnvStackEntry):
            # Find by object identity
            try:
                idx = self._env_stack.index(target)
                popped = self._env_stack[idx:]
                self._env_stack = self._env_stack[:idx]
                return popped[-1].env_name if popped else None
            except ValueError:
                return None

        return None

    def _init_macros(self):
        self._init_state_macros()
        self._init_counter_macros()
        self._init_math_macros()
        self._init_equation_tag_macros()

    def _init_equation_tag_macros(self):
        def equation_tag_handler(expander: "ExpanderCore", token: Token):
            expander.skip_whitespace()
            tag_tokens = expander.parse_brace_as_tokens(expand=True)
            if tag_tokens is None:
                return None
            tag_str = expander.convert_tokens_to_str(tag_tokens)
            return [CommandWithArgsToken("tag", numbering=tag_str)]

        def eqno_handler(expander: "ExpanderCore", token: Token):
            r"""\eqno(1.1) -> \tag{1.1}"""
            expander.skip_whitespace()
            tag_tokens = expander.parse_parenthesis_as_tokens(expand=True)
            if tag_tokens is None:
                return None
            tag_str = expander.convert_tokens_to_str(tag_tokens)
            return [CommandWithArgsToken("tag", numbering=tag_str)]

        self.register_handler("\\tag", equation_tag_handler, is_global=True)
        self.register_handler("\\eqno", eqno_handler, is_global=True)

    def _init_math_macros(self):
        def make_begin_end_math_handlers():
            out_token = Token(TokenType.MATH_SHIFT_INLINE, "$")

            def begin_math_handler(expander: "ExpanderCore", token: Token):
                expander.state.push_mode(ProcessingMode.MATH_INLINE)
                return [out_token.copy()]

            def end_math_handler(expander: "ExpanderCore", token: Token):
                if expander.is_math_mode:
                    expander.state.pop_mode()
                return [out_token.copy()]

            return begin_math_handler, end_math_handler

        inline_begin, inline_end = make_begin_end_math_handlers()

        self.register_handler("\\(", inline_begin, is_global=True)
        self.register_handler("\\)", inline_end, is_global=True)

        equation_star_tokens = convert_str_to_tokens(
            "equation*", catcode=Catcode.LETTER
        )

        def display_begin(expander: "ExpanderCore", token: Token):
            # mock \begin{equation*}
            out_tokens = wrap_tokens_in_braces(equation_star_tokens)
            expander.push_tokens([BEGIN_ENV_TOKEN.copy()] + out_tokens)
            return []

        def display_end(expander: "ExpanderCore", token: Token):
            # mock \end{equation*}
            out_tokens = wrap_tokens_in_braces(equation_star_tokens)
            expander.push_tokens([END_ENV_TOKEN.copy()] + out_tokens)
            return []

        self.register_handler("\\[", display_begin, is_global=True)
        self.register_handler("\\]", display_end, is_global=True)

    def _init_state_macros(self):
        def global_handler(expander: "ExpanderCore", token: Token):
            expander.state.pending_global = True
            return []

        def bye_handler(expander: "ExpanderCore", token: Token):
            expander.logger.info(r"\bye triggered, popped source")
            expander.stream.pop_source()
            return []

        self.register_handler("\\global", global_handler, is_global=True)
        self.register_macro("\\empty", EmptyMacro(), is_global=True)
        self.register_macro("\\@empty", EmptyMacro(), is_global=True)
        self.register_macro("\\relax", RelaxMacro(), is_global=True)
        self.register_handler("\\null", lambda expander, token: [], is_global=True)
        self.register_handler("\\protect", lambda expander, token: [], is_global=True)
        self.register_handler("\\bye", bye_handler, is_global=True)

    def _init_counter_macros(self):
        for counter_name in self.state.counter_manager.counters:
            self.register_counter_macro(counter_name, is_user_defined=False)
            self.register_macro(
                f"c@{counter_name}",
                make_the_counter_macro(counter_name, formatted=False),
                is_global=True,
            )

    def register_counter_macro(self, counter_name: str, is_user_defined=False):
        macro_name = f"the{counter_name}"

        def the_counter_handler(expander: "ExpanderCore", token: Token):
            value = expander.state.get_counter_display(
                counter_name, strict=True, hierarchy=False
            )
            if value is None:
                return None
            # if parent counter exists, use \the{parentname} to get its value
            # then append the value of the current counter
            counter_info = expander.state.get_counter_info(counter_name)
            if counter_info and counter_info.parent:
                parent_counter_name = counter_info.parent.name
                parent_value = expander.get_counter_display(
                    parent_counter_name, strict=True
                )
                if parent_value:
                    value = parent_value + "." + value
                    if counter_info.skip_parent_zeros:
                        while value.startswith("0."):
                            value = value[2:]

            return expander.convert_str_to_tokens(f"{value}")

        self.register_handler(
            macro_name,
            the_counter_handler,
            is_global=True,
            is_user_defined=is_user_defined,
        )

    # counters
    def create_new_counter(
        self, counter_name: str, parent: Optional[str] = None, is_user_defined=True
    ):
        self.state.new_counter(counter_name, parent)
        if counter_name.isalpha():
            self.register_counter_macro(counter_name, is_user_defined=is_user_defined)

    def has_counter(self, counter_name: str) -> bool:
        return self.state.has_counter(counter_name)

    def get_counter_display(
        self, counter_name: str, strict=False, filter_leading_zeros=True
    ) -> Optional[str]:
        if not strict and counter_name == "equation" and self.state.in_subequations:
            counter_name = "subequation"
        # check for \thecountername first, since it mimics latex.
        # people sometimes redefine it e.g. \renewcommand{\theequation}{\thesection.\arabic{equation}}
        name = "the" + counter_name
        the_macro = self.get_macro(name)

        counter_display_str = None
        if the_macro:
            out_tokens = self.expand_tokens([Token(TokenType.CONTROL_SEQUENCE, name)])
            if out_tokens:
                counter_display_str = self.convert_tokens_to_str(out_tokens)
        if not counter_display_str:
            counter_display_str = self.state.get_counter_display(
                counter_name, strict=strict
            )
        if counter_display_str and filter_leading_zeros:
            # filter out leading 0... e.g. 0.0.1 -> 1
            while counter_display_str.startswith("0."):
                counter_display_str = counter_display_str[2:]
        return counter_display_str

    # fonts
    def create_new_font(self, font_name: str, font_definition: List[Token]):
        self.state.font_registry[font_name] = font_definition
        # register and simply return the token as \fontname.. (for later use)
        self.register_handler(
            font_name,
            lambda expander, token: [Token(TokenType.CONTROL_SEQUENCE, font_name)],
            is_global=True,
        )

    @staticmethod
    def is_control_sequence(tok: Token) -> bool:
        return tok.type == TokenType.CONTROL_SEQUENCE or tok.catcode == Catcode.ACTIVE

    # MACROS
    @staticmethod
    def normalize_macro_name(tok_or_name: str | Token) -> tuple[str, bool] | None:
        """
        Normalize a token or string to (name, is_active_char) for macro operations.
        Returns None if the token is not a valid macro name.
        """
        if isinstance(tok_or_name, Token):
            if tok_or_name.catcode == Catcode.ACTIVE:
                return tok_or_name.value, True
            if tok_or_name.type == TokenType.CONTROL_SEQUENCE:
                return "\\" + tok_or_name.value, False
            return None
        return tok_or_name, False

    def get_macro(self, tok_or_name: str | Token) -> Optional[Macro]:
        if not tok_or_name:
            return None
        normalized = self.normalize_macro_name(tok_or_name)
        if normalized is None:
            return None
        tok_str, is_active_char = normalized
        return self.state.get_macro(tok_str, is_active_char=is_active_char)

    def delete_macro(self, tok_or_name: str | Token, is_global: bool = True):
        normalized = self.normalize_macro_name(tok_or_name)
        if normalized is None:
            return  # Invalid token type, nothing to delete
        tok_str, is_active_char = normalized
        self.state.delete_macro(
            tok_str, is_global=is_global, is_active_char=is_active_char
        )

    def get_all_macros(self) -> Dict[str, Macro]:
        return self.state.get_all_macros()

    def register_macro(
        self,
        tok_or_name: str | Token,
        macro: Macro,
        is_global: bool = False,
        is_user_defined: bool = False,
    ):
        normalized = self.normalize_macro_name(tok_or_name)
        if normalized is None:
            return  # Invalid token type, cannot register
        tok_str, is_active_char = normalized
        macro.is_user_defined = is_user_defined

        self.state.set_macro(
            tok_str, macro, is_global=is_global, is_active_char=is_active_char
        )

    def register_handler(
        self,
        tok_or_name: str | Token,
        handler: Handler,
        is_global: bool = False,
        is_user_defined: bool = False,
    ):
        normalized = self.normalize_macro_name(tok_or_name)
        if normalized is None:
            return  # Invalid token type, cannot register
        tok_str, is_active_char = normalized
        macro = Macro(tok_str, handler, is_user_defined=is_user_defined)
        self.state.set_macro(
            tok_str, macro, is_global=is_global, is_active_char=is_active_char
        )

    def check_macro_is_user_defined(self, tok_or_name: str | Token) -> bool:
        macro = self.get_macro(tok_or_name)
        if macro is None:
            return False
        return macro.is_user_defined

    def substitute_token_args(
        self, tokens: List[Token], args: List[List[Token]]
    ) -> List[Token]:
        is_math = self.is_math_mode
        tokens = [t.copy() for t in tokens]
        if is_math:
            # convert token definitions to mathmode catcodes
            for i, token in enumerate(tokens):
                if token.type == TokenType.CONTROL_SEQUENCE:
                    continue
                elif len(token.value) > 1:
                    continue
                ord_char = ord(token.value)
                if ord_char in MATHMODE_CATCODES:
                    token.catcode = MATHMODE_CATCODES[ord_char]

        out = substitute_token_args(tokens, args)
        return out

    # Colors
    def get_colors(self):
        return self.state.color_registry.copy()

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
        if isinstance(value, list):  # should be a list of tokens
            if value and not isinstance(value[0], Token):
                self.logger.warning(
                    f"Register '{reg_id}' is not a list of Tokens, returning []"
                )
                return []
            return value
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
    def clear(self):
        self.stream.clear()

    def set_text(self, text: str):
        self.stream.set_text(text)

    def eof(self) -> bool:
        return self.stream.eof()

    def expand(self, text: str) -> List[Token]:
        self.set_text(text)
        return self.process()

    def makeatletter(self) -> List[Token]:
        self.set_catcode(ord("@"), Catcode.LETTER)
        return []

    def makeatother(self) -> List[Token]:
        self.set_catcode(ord("@"), Catcode.OTHER)
        return []

    def expand_ltx(self, text: str, source_file: Optional[str] = None) -> List[Token]:
        """
        Expand LaTeX internal code that may contain @ symbols.
        """

        old_catcode = self.get_catcode(ord("@"))
        self.makeatletter()
        result = self.expand_text(text, source_file=source_file)
        self.set_catcode(ord("@"), old_catcode)
        return result

    @staticmethod
    def _generate_stop_token():
        # this control sequence is invalid in latex, so we can use it as an arbitrary stop token
        return Token(TokenType.CONTROL_SEQUENCE, f"\\@#STOP", catcode=Catcode.OTHER)

    def expand_text(self, text: str, source_file: Optional[str] = None) -> List[Token]:
        STOP_TOKEN = self._generate_stop_token()
        self.push_tokens([STOP_TOKEN])
        self.push_text(text, source_file=source_file)
        # use `tok is STOP_TOKEN` to check for identity
        out = self.process(
            stop_token_logic=lambda tok: tok is STOP_TOKEN, consume_stop_token=True
        )
        return out

    def expand_tokens(self, tokens: List[Token]) -> List[Token]:
        if not tokens:
            return []
        STOP_TOKEN = self._generate_stop_token()
        self.push_tokens(tokens + [STOP_TOKEN])
        # use `tok is STOP_TOKEN` to check for identity
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
                if stop_token_logic:
                    for i, token in enumerate(processed):
                        if stop_token_logic(token):
                            if consume_stop_token:
                                i += 1
                            self.push_tokens(processed[i:])
                            return final_expanded_tokens
                        final_expanded_tokens.append(token)
                else:
                    final_expanded_tokens.extend(processed)

        return final_expanded_tokens

    def expand_until(
        self, stop_token_logic: TokenPredicate, consume_stop_token: bool = True
    ) -> List[Token]:
        return self.process(stop_token_logic, consume_stop_token=consume_stop_token)

    def expand_until_eol_or_relax(self, skip_whitespace: bool = True) -> List[Token]:
        out: List[Token] = []
        while not self.eof():
            tokens = self.expand_next()
            if not tokens:
                break

            exit = False
            for i, tok in enumerate(tokens):
                # if encounter any tokens that have been expanded, return and exit
                if self.is_relax_token(tok):
                    self.push_tokens(tokens[i + 1 :])
                    exit = True
                    break
                elif tok.type == TokenType.END_OF_LINE:
                    self.push_tokens(tokens[i:])
                    exit = True
                    break
                elif not skip_whitespace and is_whitespace_token(tok):
                    self.push_tokens(tokens[i:])
                    exit = True
                    break
                else:
                    out.append(tok)

            if exit:
                break

        return out

    def push_scope(self):
        self.state.push_scope()

    def pop_scope(self):
        self.state.pop_scope()

    def push_tokens(self, tokens: List[Token]):
        self.stream.push_tokens([t for t in tokens if t is not None])

    def push_text(self, text: str, source_file: Optional[str] = None):
        if source_file:
            # Ensure source_file is relative to cwd if within cwd, otherwise keep absolute
            abs_source = os.path.abspath(source_file)
            abs_cwd = os.path.abspath(self.cwd)

            rel_path = os.path.relpath(abs_source, abs_cwd)
            # Only use relative path if it doesn't start with '..' (i.e., is within cwd)
            source_file = rel_path if not rel_path.startswith("..") else abs_source
        self.stream.push_text(text, source_file=source_file)

    def get_cwd_path(self, file_path: str) -> str:
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.cwd, file_path)
        return file_path

    def resolve_file_path(
        self, file_path: str, default_extension: str = ".tex"
    ) -> Optional[str]:
        # Convert Path objects to string
        file_path = str(file_path)
        file_path = self.get_cwd_path(file_path)
        ext = os.path.splitext(file_path)[1].lower()

        # If no extension or invalid extension, try to resolve the file
        if not ext or ext not in self.VALID_LATEX_EXTENSIONS:
            file_path_with_ext = file_path + default_extension
            if os.path.exists(file_path_with_ext):
                return file_path_with_ext
            elif os.path.exists(file_path):
                # Original path exists (maybe it's a file without extension)
                return file_path
            else:
                # Neither exists
                return None

        # Has valid extension, check if exists
        if os.path.exists(file_path):
            return file_path

        return None

    def if_file_exists(self, file_path: str, default_extension: str = ".tex") -> bool:
        return self.resolve_file_path(file_path, default_extension) is not None

    def push_file(self, file_path: str, extension: str = ".tex"):
        """Push a file onto the token stream.

        Args:
            file_path: The file path to push
            extension: The default extension to use if file has no extension
        """
        resolved_path = self.resolve_file_path(file_path, extension)

        if resolved_path is None:
            # File doesn't exist, construct path with extension and let read_file handle the error
            file_path = self.get_cwd_path(file_path)
            ext = os.path.splitext(file_path)[1].lower()
            resolved_path = file_path if ext else file_path + extension

        ext = os.path.splitext(resolved_path)[1].lower()

        # Handle package or class files
        if ext == ".sty":
            self.load_package(resolved_path, extension=ext)
            return
        elif ext == ".cls":
            self.load_class(resolved_path, extension=ext)
            return

        # Load regular file
        input_text = self.read_file(resolved_path)
        if input_text is None:
            return
        # ensure to put \n at the end of the file to delimit/split, in case file ends with %
        self.push_text(input_text + "\n", source_file=resolved_path)

    def expand_file(self, file_path: str, is_package_or_class: bool = False):
        # Determine default extension based on file type
        default_ext = ".sty" if is_package_or_class else ".tex"
        resolved_path = self.resolve_file_path(file_path, default_ext)

        if resolved_path is None:
            self.logger.warning(f"Input file {file_path} does not exist")
            return None

        self.logger.info("EXPANDING FILE " + resolved_path)
        input_text = self.read_file(resolved_path)
        if input_text is None:
            return None

        # strip comments to avoid parsing errors since some files may contain
        # comments that can affect the input stream. To investigate at a future date
        input_text = strip_latex_comments(input_text).strip()
        if not input_text:
            return None

        if is_package_or_class:
            return self.expand_ltx(input_text, source_file=resolved_path)

        return self.expand_text(input_text, source_file=resolved_path)

    def read_file(self, file_path: str) -> Optional[str]:
        if not os.path.exists(file_path):
            self.logger.warning(f"Input file {file_path} does not exist")
            return None
        is_supported, error_msg = is_supported_tex_version(file_path)
        if not is_supported:
            self.logger.error(f"Unsupported TeX version {file_path}: {error_msg}")
            return None
        try:
            return read_file(file_path)
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {e}")
            return None

    def _load_package_or_class(
        self,
        package_or_class_name: str,
        extension: str,
        is_package: bool,
        read_file=True,
    ) -> Optional[List[Token]]:
        loaded_set = self.loaded_packages if is_package else self.loaded_classes
        if package_or_class_name in loaded_set:
            return None

        package_path = package_or_class_name
        if not package_path.endswith(extension):
            package_path += extension

        # Strip extension and path to just get base name
        base_name = os.path.splitext(os.path.basename(package_or_class_name))[0]
        loaded_set.add(base_name)

        self.logger.debug(f"Loading package/class: {package_path}")

        if read_file and self.if_file_exists(package_path, extension):
            was_in_package_or_class = self.state.in_package_or_class
            self.state.in_package_or_class = True
            # self.push_scope()
            tokens = self.expand_file(package_path, is_package_or_class=True)
            # self.pop_scope()

            self.state.in_package_or_class = was_in_package_or_class

            return tokens

        return None

    def load_package(
        self, package_name: str, read_file=True, extension: Optional[str] = ".sty"
    ):
        return self._load_package_or_class(
            package_name, extension or ".sty", is_package=True, read_file=read_file
        )

    def load_class(
        self, class_name: str, read_file=True, extension: Optional[str] = ".cls"
    ):
        return self._load_package_or_class(
            class_name, extension or ".cls", is_package=False, read_file=read_file
        )

    def peek(self, offset: int = 0) -> Optional[Token]:
        return self.stream.peek(offset)

    def consume(self) -> Optional[Token]:
        return self.stream.consume()

    def skip_whitespace(self):
        self.stream.skip_whitespace()

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

    # main parsing logic
    def expand_next(self) -> Optional[List[Token]]:
        tok = self.parse_token()
        if tok is None:
            return None

        # if self.state.is_verbatim_mode:
        #     return [tok]

        if self.is_control_sequence(tok):
            return self._exec_macro(tok)
        else:
            self.state.pending_global = False
            # Pop scope when we encounter an EnvironmentEndToken that needs it
            # This completes the environment scope lifecycle:
            #   1. begin_environment_handler pushes scope
            #   2. begin_definition and body are processed (scope active)
            #   3. end_definition is processed (scope still active - can access scoped macros)
            #   4. EnvironmentEndToken is encountered HERE - scope is popped
            # The flag ensures we only pop for "fresh" end tokens, not reprocessed ones
            if tok.type == TokenType.ENVIRONMENT_END:
                from latex2json.tokens.types import EnvironmentEndToken
                if isinstance(tok, EnvironmentEndToken) and hasattr(tok, 'should_pop_scope') and tok.should_pop_scope:
                    self.pop_env_stack(tok.value)
                    self.pop_scope()
                    # Clear the flag so we don't pop again if token is reprocessed
                    tok.should_pop_scope = False
            elif is_begin_group_token(tok):
                self.push_scope()
            elif is_end_group_token(tok):
                self.pop_scope()
            elif tok.type == TokenType.MATH_SHIFT_INLINE:
                next_tok = self.peek()
                # check consecutive $$, and ensure not in existing inline mode
                if (
                    next_tok
                    and next_tok.type == TokenType.MATH_SHIFT_INLINE
                    and not self.state.mode == ProcessingMode.MATH_INLINE
                ):
                    self.consume()
                    self.state.toggle_mode(ProcessingMode.MATH_DISPLAY)
                    return [Token(TokenType.MATH_SHIFT_DISPLAY, "$$")]
                self.state.toggle_mode(ProcessingMode.MATH_INLINE)
        return [tok]

    def _exec_macro(self, tok: Token) -> Optional[List[Token]]:
        macro = self.get_macro(tok)
        if macro and macro.handler:
            return macro.handler(self, tok)
        return [tok]

    def next_non_expandable_tokens(self) -> Optional[List[Token]]:
        while not self.eof():
            out = self.expand_next()
            if out and len(out) > 0:
                # assign source file to tokens if not already set
                current_source_file = self.stream.get_current_source_file()
                if current_source_file:
                    for tok in out:
                        if not tok.source_file:
                            tok.source_file = current_source_file
                return out
        return None

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

    # parser helper functions
    def match(
        self,
        token_type: Optional[TokenType] = None,
        value: Optional[str] = None,
        catcode: Optional[Catcode] = None,
    ) -> bool:
        return self.stream.match(token_type, value, catcode)

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
        out = ""

        last_exp = None
        while not self.eof():
            tok = self.peek()
            if tok_cur_str_predicate(tok, out):
                self.consume()
                out += tok.value
            elif self.is_control_sequence(tok):
                # if we see a declaration macro e.g. \def or \newcommand, exit
                macro = self.get_macro(tok)
                if macro and macro.type == MacroType.DECLARATION:
                    return out, False

                # check \relax token and that it is RelaxMacro i.e. has not been redefined
                if self.is_relax_token(tok):
                    self.consume()  # consume \relax token itself
                    return out, True

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
        return out, False

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
                base_scaled_points += plus_scaled_points
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
                base_scaled_points -= minus_scaled_points
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
            brace_depth = 1  # We've consumed one opening brace, so depth starts at 1

            # 3. Loop until the matching closing brace is found (brace_depth returns to 0)
            while brace_depth > 0:
                current_token = self.peek()

                if current_token is None:
                    # Error: Reached the end of the input stream before finding a matching closing brace.
                    self.logger.info(
                        "Expander - Unmatched braces: Reached end of stream within a definition."
                    )
                    # Depending on your error handling strategy, you might raise an exception here
                    # or return the partially collected tokens.
                    break  # Exit loop due to error

                # Check token type and update brace_depth
                if begin_predicate(current_token):
                    brace_depth += 1
                elif end_predicate(current_token):
                    brace_depth -= 1

                current_token = self.parse_token(verbatim=verbatim)

                if brace_depth > 0:
                    out_tokens.append(current_token)

            return out_tokens
        finally:
            self._reset_verbatim_mode_context(verbatim)

    def parse_brace_as_tokens(
        self, expand=False, verbatim=False
    ) -> Optional[List[Token]]:
        tokens = self.parse_begin_end_as_tokens(
            is_begin_group_token, is_end_group_token, verbatim=verbatim
        )
        if expand and tokens:
            tokens = self.expand_tokens(tokens)
        return tokens

    def parse_bracket_as_tokens(
        self, expand=False, verbatim=False
    ) -> Optional[List[Token]]:
        tokens = self.parse_begin_end_as_tokens(
            is_begin_bracket_token, is_end_bracket_token, verbatim=verbatim
        )
        if expand and tokens:
            tokens = self.expand_tokens(tokens)
        return tokens

    def parse_parenthesis_as_tokens(
        self, expand=False, verbatim=False
    ) -> Optional[List[Token]]:
        tokens = self.parse_begin_end_as_tokens(
            is_begin_parenthesis_token, is_end_parenthesis_token, verbatim=verbatim
        )
        if expand and tokens:
            tokens = self.expand_tokens(tokens)
        return tokens

    def set_catcode(self, char_ord: int, catcode: Catcode):
        self.state.set_catcode(char_ord, catcode)

    def get_catcode(self, char_ord: int) -> Catcode:
        return self.state.get_catcode(char_ord)

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

    def convert_str_to_tokens(
        self, text: str, catcode: Optional[Catcode] = None
    ) -> List[Token]:
        out = []
        for t in text:
            c = catcode or self.get_catcode(ord(t))
            out.append(Token(TokenType.CHARACTER, t, catcode=c))
        return out

    @staticmethod
    def convert_tokens_to_str(tokens: List[Token]) -> str:
        return "".join(t.to_str() for t in tokens if t is not None)

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

    def get_environment_definition(
        self, env_name: str
    ) -> Optional[EnvironmentDefinition]:
        return self.state.get_environment_definition(env_name)

    def get_parent_float_env(self) -> Optional[EnvironmentDefinition]:
        env_stack = self.get_env_stack()
        for env in reversed(env_stack):
            env_def = self.get_environment_definition(env)
            if env_def and env_def.is_float_env:
                return env_def
        return None

    def register_environment(
        self,
        env_name: str,
        env_def: EnvironmentDefinition,
        is_global: bool = True,
        is_user_defined: bool = False,
    ) -> None:
        """Register a new environment with begin/end handlers."""
        self.state.set_environment_definition(env_name, env_def)

        counter_name = env_def.counter_name
        if counter_name:
            self.create_new_counter(counter_name)

        # Only create default handlers if custom handlers are not already set
        if env_def.begin_handler is None:

            def begin_handler(expander: "ExpanderCore", token: Token) -> List[Token]:
                # Use shared environment processing logic
                from latex2json.expander.handlers.environment.environment_utils import (
                    process_environment_begin,
                )

                return process_environment_begin(
                    expander, token, env_name, env_def, expand_begin_definition=True
                )

            # attach the handler to the envdef instance
            env_def.begin_handler = begin_handler

        if env_def.end_handler is None:

            def end_handler_impl(
                expander: "ExpanderCore", token: Token, env_name_param: str
            ) -> List[Token]:
                # Use shared environment end processing logic
                from latex2json.expander.handlers.environment.environment_utils import (
                    process_environment_end,
                )

                return process_environment_end(expander, token, env_name_param, env_def)

            # attach the handler to the envdef instance
            env_def.end_handler = end_handler_impl

        if env_def.has_direct_command and env_name.isalpha():
            self.register_macro(
                env_name,
                Macro(env_name, env_def.begin_handler, env_def.begin_definition),
                is_global=is_global,
                is_user_defined=is_user_defined,
            )

            # Create a wrapper for direct end commands (like \endhello)
            # that extracts the env name and calls the end_handler
            def make_end_macro_handler(env_name_captured: str):
                def end_macro_handler(expander: "ExpanderCore", token: Token) -> List[Token]:
                    # Extract env name from token (remove "end" prefix)
                    name = token.value[3:] if token.value.startswith("end") else env_name_captured
                    return env_def.end_handler(expander, token, name)
                return end_macro_handler

            self.register_macro(
                "end" + env_name,
                Macro("end" + env_name, make_end_macro_handler(env_name), env_def.end_definition),
                is_global=is_global,
                is_user_defined=is_user_defined,
            )

        if env_def.begin_command:
            self.register_macro(
                env_def.begin_command,
                Macro(
                    env_def.begin_command,
                    env_def.begin_handler,
                    env_def.begin_definition,
                ),
                is_global=is_global,
                is_user_defined=is_user_defined,
            )

        if env_def.end_command:
            # Wrap end_handler to provide env_name for custom end commands
            def make_end_cmd_handler(env_name_captured: str):
                def end_cmd_handler(expander: "ExpanderCore", token: Token) -> List[Token]:
                    return env_def.end_handler(expander, token, env_name_captured)
                return end_cmd_handler

            self.register_macro(
                env_def.end_command,
                Macro(env_def.end_command, make_end_cmd_handler(env_name), env_def.end_definition),
                is_global=is_global,
                is_user_defined=is_user_defined,
            )

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


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    # base component only
    text = r"""
\makeatletter
\def\@maketitle{
    \begin{tabular}[t]{c}\@author
    \end{tabular}
}
\def\maketitle{
    \@maketitle
}

\title{Caffe: Convolutional Architecture}

\def\alignauthor{
    \end{tabular}
  \begin{tabular}[t]{c}
}

\author{
    \alignauthor Yangqing Jia \\
}

\maketitle

\begin{abstract}
Caffe Abstract
\end{abstract}
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
