"""Mixin providing expansion/processing logic for ExpanderCore."""

from __future__ import annotations

from collections import deque
from typing import Any, Callable, List, Optional, TYPE_CHECKING

from latex2json.expander.macro_registry import Macro
from latex2json.expander.state import ProcessingMode
from latex2json.expander.amstex_expander import AMSTeXExpander
from latex2json.tokens import Catcode, Token, TokenType
from latex2json.tokens.utils import (
    is_begin_group_token,
    is_end_group_token,
    is_whitespace_token,
)

if TYPE_CHECKING:
    from latex2json.expander.expander_core import ExpanderCore

TokenPredicate = Callable[[Token], bool]


class ExpansionMixin:
    """Expansion and processing logic mixed into ExpanderCore."""

    if TYPE_CHECKING:
        _recent_tokens: deque
        _recursion_threshold: int
        _token_count: int
        _env_stack: list
        state: Any
        stream: Any
        logger: Any

        def peek(self) -> Optional[Token]: ...
        def consume(self) -> Optional[Token]: ...
        def eof(self) -> bool: ...
        def is_control_sequence(self, tok: Token) -> bool: ...
        def get_macro(self, tok_or_name) -> Optional[Macro]: ...
        def push_tokens(self, tokens: List[Token]) -> None: ...
        def push_text(self, text: str, source_file: Optional[str] = None, preprocess_amstex: bool = True) -> None: ...
        def set_text(self, text: str, source_file: Optional[str] = None) -> None: ...
        def push_scope(self) -> None: ...
        def pop_scope(self) -> None: ...
        def pop_env_stack(self, target=None): ...
        def parse_token(self, verbatim: bool = False) -> Optional[Token]: ...
        def is_relax_token(self, token: Token) -> bool: ...
        def makeatletter(self) -> List[Token]: ...
        def set_catcode(self, char_ord: int, catcode: Catcode) -> None: ...
        def get_catcode(self, char_ord: int) -> Catcode: ...

        @property
        def is_math_mode(self) -> bool: ...

    # PROCESSING
    def expand(self, text: str) -> List[Token]:
        """Expand text and return resulting tokens."""
        self.set_text(text)
        return self.process()

    def expand_ltx(self, text: str, source_file: Optional[str] = None) -> List[Token]:
        """Expand LaTeX internal code that may contain @ symbols."""
        old_catcode = self.get_catcode(ord("@"))
        self.makeatletter()
        result = self._expand_latex_text(text, source_file=source_file)
        self.set_catcode(ord("@"), old_catcode)
        return result

    @staticmethod
    def _generate_stop_token():
        # this control sequence is invalid in latex, so we can use it as an arbitrary stop token
        return Token(TokenType.CONTROL_SEQUENCE, f"\\@#STOP", catcode=Catcode.OTHER)

    def expand_text(self, text: str, source_file: Optional[str] = None) -> List[Token]:
        """Expand text with source file attribution."""
        return self._expand_latex_text(text, source_file=source_file)

    def _expand_latex_text(
        self, text: str, source_file: Optional[str] = None
    ) -> List[Token]:
        STOP_TOKEN = self._generate_stop_token()
        self.push_tokens([STOP_TOKEN])
        self.push_text(text, source_file=source_file, preprocess_amstex=False)
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

    def _preprocess_amstex(
        self, text: str, source_file: Optional[str] = None
    ) -> List[Token]:
        """
        Preprocess AMSTeX text to LaTeX tokens (NOT expanded).

        Uses a fresh tokenizer to isolate AMSTeX preprocessing from any
        catcode changes in the main document.
        """
        self.logger.info(
            f"Preprocessing AMSTeX to LaTeX{f' from {source_file}' if source_file else ''}..."
        )

        amstex = AMSTeXExpander(logger=self.logger)

        tokens = amstex.process_text(text)

        if source_file:
            for tok in tokens:
                if not tok.source_file:
                    tok.source_file = source_file

        if self.get_macro("\\proclaim") is None and "\\proclaim" in text:
            # inject proclaim -> newtheorem latex hack
            pretext = r"""
            \newcommand\proclaim[1]{%
            \newtheorem{#1}{#1}
            \renewcommand\endproclaim{\end{#1}}
            \begin{#1}%
            }
            """
            self._expand_latex_text(pretext)

        return tokens

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

    # main expansion logic
    def _check_recursion(self, tok: Token) -> None:
        r"""Check if we're in an infinite recursion loop.

        Detects when tokens from the SAME source position keep repeating, which indicates
        infinite macro expansion. Different source positions are fine (e.g., 100 different
        \DeclareMathOperator calls from different lines).

        Args:
            tok: The token being processed

        Raises:
            RuntimeError: If infinite recursion is detected
        """
        # Skip whitespace tokens to reduce noise
        if tok.type == TokenType.CHARACTER and tok.catcode == Catcode.SPACE:
            return
        if tok.type == TokenType.END_OF_LINE:
            return

        # Sample every 10th significant token to reduce overhead
        self._token_count += 1
        if self._token_count % 10 != 0:
            return

        # Create a hashable token signature: (type, value, catcode, position)
        # INCLUDE POSITION: This differentiates between:
        # - \DeclareMathOperator at line 10 (position X)
        # - \DeclareMathOperator at line 11 (position Y)
        # These are different! Only same position repeating = infinite loop
        token_sig = (tok.type, tok.value, tok.catcode, tok.position)

        # Add to recent tokens
        self._recent_tokens.append(token_sig)

        # Check for patterns periodically once we have enough tokens
        # Checking every token is expensive, so we batch the checks
        if len(self._recent_tokens) >= 500 and len(self._recent_tokens) % 100 == 0:
            self._check_for_repeating_pattern()

    def _check_for_repeating_pattern(self) -> None:
        """Check if recent tokens contain a repeating pattern."""
        # Try different sequence lengths (from 1 to half the buffer size)
        # We check if the same sequence repeats N times
        recent_list = list(self._recent_tokens)

        for seq_len in range(1, len(recent_list) // (self._recursion_threshold) + 1):
            # Check if the last seq_len * threshold tokens form a repeating pattern
            total_len = seq_len * self._recursion_threshold
            if total_len > len(recent_list):
                break

            # Extract the most recent tokens
            recent_segment = recent_list[-total_len:]

            # Check if it's a repeating pattern
            pattern = recent_segment[:seq_len]
            is_repeating = True

            for i in range(self._recursion_threshold):
                segment = recent_segment[i * seq_len : (i + 1) * seq_len]
                if segment != pattern:
                    is_repeating = False
                    break

            if is_repeating:
                # Format error message with context
                pattern_str = " ".join(f"'{sig[1]}'" for sig in pattern)
                error_msg = (
                    f"Infinite recursion detected: sequence [{pattern_str}] "
                    f"has repeated {self._recursion_threshold} times without making progress.\n"
                    f"This likely indicates an infinite expansion loop in the LaTeX code."
                )
                raise RuntimeError(error_msg)

    def expand_next(self) -> Optional[List[Token]]:
        tok = self.parse_token()
        if tok is None:
            return None

        # Check for infinite recursion before processing
        self._check_recursion(tok)

        # if self.state.is_verbatim_mode:
        #     return [tok]

        if self.is_control_sequence(tok):
            # Get macro once and pass to _exec_macro to avoid redundant lookup
            macro = self.get_macro(tok)
            return self._exec_macro(tok, macro)
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

                if (
                    isinstance(tok, EnvironmentEndToken)
                    and hasattr(tok, "should_pop_scope")
                    and tok.should_pop_scope
                ):
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

    def _exec_macro(
        self, tok: Token, macro: Optional[Macro] = None
    ) -> Optional[List[Token]]:
        # Accept macro as parameter to avoid redundant lookup
        if macro is None:
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
