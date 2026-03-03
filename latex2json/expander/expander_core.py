from collections import deque
from dataclasses import dataclass
from logging import Logger
from typing import Callable, List, Any, Dict, Optional, Set, Union

from latex2json.tokens.catcodes import MATHMODE_CATCODES
from latex2json.tokens.types import BEGIN_ENV_TOKEN, END_ENV_TOKEN, CommandWithArgsToken
from latex2json.tokens.utils import (
    convert_str_to_tokens,
    strip_whitespace_tokens,
    substitute_token_args,
    wrap_tokens_in_braces,
)
from latex2json.expander.macro_registry import (
    EmptyMacro,
    Handler,
    Macro,
    MacroRegistry,
    MacroType,
    RelaxMacro,
)

from latex2json.latex_maps.environments import EnvironmentDefinition
from latex2json.registers import (
    RegisterType,
    TexRegisters,
)

from latex2json.expander.state import ExpanderState, ProcessingMode
from latex2json.expander.utils import RELAX_TOKEN
from latex2json.tokens import Catcode, Token, TokenType, Tokenizer
from latex2json.expander.token_processor import TokenProcessor
from latex2json.expander._parsing_mixin import ParsingMixin
from latex2json.expander._file_io_mixin import FileIOMixin
from latex2json.expander._expansion_mixin import ExpansionMixin
from latex2json.utils.tex_versions import is_content_amstex

TokenPredicate = Callable[[Token], bool]


@dataclass
class EnvStackEntry:
    """Entry in the environment stack tracking nested environments."""

    env_name: str  # The environment name (e.g., "figure", "table")
    opening_token: (
        Token  # The token that opened this environment (\begin, \@float, etc.)
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


class ExpanderCore(ExpansionMixin, ParsingMixin, FileIOMixin, TokenProcessor):
    """
    The main engine for processing the document.
    Drives parsing, manages state, executes commands, and performs expansion.

    Inherits token stream operations and parsing helpers from TokenProcessor.
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
        # Initialize base class (sets up tokenizer, stream, logger)
        super().__init__(tokenizer=tokenizer, logger=logger)
        self.state = ExpanderState(self.tokenizer, logger=self.logger)

        self.cwd = "."
        self.project_root = "."
        self.loaded_packages: Set[str] = set()
        self.loaded_classes: Set[str] = set()

        # Recursion detection: track recent tokens to detect infinite loops
        self._recent_tokens: deque = deque(maxlen=1000)  # Track last 1000 tokens
        self._recursion_threshold = 100  # Number of times a sequence must repeat
        self._token_count = 0  # Counter for sampling optimization
        # Since we track full token sequences (not just control sequences),
        # different commands create different patterns, avoiding false positives

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
        self.register_handler("\\protected", lambda expander, token: [], is_global=True)
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

        # Register c@{counter} as a RegisterMacro so \ifnum, \advance, etc. can use it
        from latex2json.expander.handlers.registers.counter_handlers import (
            register_counter_register_macro,
        )

        internal_name = f"c@{counter_name}"
        register_counter_register_macro(self, internal_name)

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

    def makeatletter(self) -> List[Token]:
        self.set_catcode(ord("@"), Catcode.LETTER)
        return []

    def makeatother(self) -> List[Token]:
        self.set_catcode(ord("@"), Catcode.OTHER)
        return []

    def push_scope(self):
        self.state.push_scope()

    def pop_scope(self):
        self.state.pop_scope()

    def push_tokens(self, tokens: List[Token]):
        self.stream.push_tokens([t for t in tokens if t is not None])

    def push_text(
        self,
        text: str,
        source_file: Optional[str] = None,
        preprocess_amstex: bool = True,
    ):
        """
        Push text onto the stream, preprocessing AMSTeX if detected.

        AMSTeX content is automatically converted to LaTeX tokens before pushing.
        """
        source_file = self._normalize_source_path(source_file)

        if preprocess_amstex and is_content_amstex(text):
            tokens = self._preprocess_amstex(text, source_file=source_file)
            self.push_tokens(tokens)
        else:
            self.stream.push_text(text, source_file=source_file)

    def set_text(self, text: str, source_file: Optional[str] = None):
        """
        Reset stream with new text.

        Unlike push_text which appends, this clears existing content first.
        """
        self.stream.clear()
        self.push_text(text, source_file=source_file)

    def set_catcode(self, char_ord: int, catcode: Catcode):
        self.state.set_catcode(char_ord, catcode)

    def get_catcode(self, char_ord: int) -> Catcode:
        return self.state.get_catcode(char_ord)

    def convert_str_to_tokens(
        self, text: str, catcode: Optional[Catcode] = None
    ) -> List[Token]:
        out = []
        for t in text:
            c = catcode or self.get_catcode(ord(t))
            out.append(Token(TokenType.CHARACTER, t, catcode=c))
        return out

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
                def end_macro_handler(
                    expander: "ExpanderCore", token: Token
                ) -> List[Token]:
                    # Extract env name from token (remove "end" prefix)
                    name = (
                        token.value[3:]
                        if token.value.startswith("end")
                        else env_name_captured
                    )
                    return env_def.end_handler(expander, token, name)

                return end_macro_handler

            self.register_macro(
                "end" + env_name,
                Macro(
                    "end" + env_name,
                    make_end_macro_handler(env_name),
                    env_def.end_definition,
                ),
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
                def end_cmd_handler(
                    expander: "ExpanderCore", token: Token
                ) -> List[Token]:
                    return env_def.end_handler(expander, token, env_name_captured)

                return end_cmd_handler

            self.register_macro(
                env_def.end_command,
                Macro(
                    env_def.end_command,
                    make_end_cmd_handler(env_name),
                    env_def.end_definition,
                ),
                is_global=is_global,
                is_user_defined=is_user_defined,
            )

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
