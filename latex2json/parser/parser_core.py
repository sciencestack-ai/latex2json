from typing import Any, Callable, List, Optional
from latex2json.nodes import (
    ASTNode,
    BraceNode,
    BracketNode,
    CommandNode,
    EnvironmentNode,
    EquationNode,
    TextNode,
    MathShiftNode,
    DimensionNode,
    EndOfLineNode,
    ArgNode,
)
from latex2json.tokens import TokenStream, Tokenizer, Catcode, Token, TokenType
from latex2json.tokens.types import (
    WHITESPACE_TOKEN,
    BEGIN_BRACE_TOKEN,
    BEGIN_BRACKET_TOKEN,
    END_BRACE_TOKEN,
    END_BRACKET_TOKEN,
    BEGIN_ENV_TOKEN,
    END_ENV_TOKEN,
)
from latex2json.tokens.utils import (
    is_text_token,
    is_integer_token,
    is_digit_token,
    is_param_token,
)


class ParserCore:
    def __init__(self, tokenizer: Tokenizer = Tokenizer()):
        """
        Initializes the ParserCore.
        Requires a CatcodeTokenizer instance (used by parse_text).
        """
        # The tokenizer is used by the parse_text helper method for testing
        self.tokenizer = tokenizer
        self.stream = TokenStream(tokenizer)

    def set_text(self, text: str):
        self.stream.set_text(text)

    def set_catcode(self, char_code: int, catcode: Catcode):
        self.stream.set_catcode(char_code, catcode)

    def get_catcode(self, char_code: int) -> Catcode:
        return self.stream.get_catcode(char_code)

    def parse_text(self, text: str) -> List[ASTNode]:
        """
        Convenience: tokenizes the text using the injected tokenizer,
        creates a stream, and parses it. Useful for testing.
        """
        self.stream.set_text(text)
        return self.parse()

    def set_pos(self, pos: int):
        self.stream.set_pos(pos)

    def eof(self) -> bool:
        return self.stream.eof()

    def parse(self) -> List[ASTNode]:
        """
        Parses the token stream into a list of AST nodes.
        This method processes the entire stream available.
        """
        if self.stream is None:
            raise ValueError("Stream is not set")

        nodes: List[ASTNode] = []
        # Loop until the end of the stream of tokens (TokenStream.eof handles ignored)
        while not self.stream.eof():
            # skip_ignored is now handled internally by TokenStream.peek/consume
            # self.skip_ignored()

            tok = self.peek()  # TokenStream.peek handles skipping ignored
            if tok is None:  # Reached end of stream after skipping
                break

            # Parse the next element based on the token type and catcode
            element = self.parse_element()

            if element:  # parse_element might return None for ignored tokens or errors
                nodes.append(element)

        return nodes

    # skip_whitespace method remains, using stream peek/consume
    def skip_whitespace(self) -> int:
        """Skips over consecutive space tokens (Catcode 10)."""
        return self.stream.skip_whitespace()

    # skip_ignored method is no longer needed here if TokenStream handles it
    # def skip_ignored(self):
    #     """Skips over tokens that should be ignored (e.g., comments, catcode 9)."""
    #     pass # Logic moved to TokenStream

    # consume and peek methods now rely on the TokenStream handling ignored tokens
    def consume(self) -> Optional[Token]:
        """Consumes and returns the next non-ignored token from the stream."""
        return self.stream.consume()  # TokenStream.consume handles skipping ignored

    def peek(self) -> Optional[Token]:
        """Peeks at the next non-ignored token without consuming it."""
        return self.stream.peek()  # TokenStream.peek handles skipping ignored

    def match_token(self, tok: Token) -> bool:
        """Checks if the next non-ignored token matches the given token."""
        return self.match(
            token_type=tok.type,
            value=tok.value,
            catcode=tok.catcode,
        )

    # The match method now checks against the new Token structure (type and catcode)
    def match(
        self,
        token_type: Optional[TokenType] = None,
        value: Optional[str] = None,
        catcode: Optional[Catcode] = None,
    ) -> bool:
        """
        Checks if the next non-ignored token matches the criteria.
        Can match by TokenType, Catcode, or Value.
        """
        # skip whitespace?
        start_pos = self.skip_whitespace()

        tok = self.peek()  # TokenStream.peek handles skipping ignored
        if tok is None:
            self.set_pos(start_pos)
            return False

        type_match = token_type is None or tok.type == token_type
        catcode_match = catcode is None or tok.catcode == catcode
        value_match = value is None or tok.value == value

        # For CHARACTER tokens, catcode is the primary discriminator after type
        is_match = False
        if tok.type == TokenType.CHARACTER:
            is_match = type_match and catcode_match and value_match
            # Value match is less common for characters
        # For CONTROL_SEQUENCE tokens, value is the primary discriminator after type
        elif tok.type == TokenType.CONTROL_SEQUENCE:
            is_match = type_match and value_match
            # Catcode is implicitly 0 for the backslash, not on the token itself
        # Default for other token types (if any)
        else:
            is_match = (
                type_match and value_match
            )  # Or adjust based on other token types

        if is_match:
            return True

        self.set_pos(start_pos)
        return False

    # parse_immediate_token might need rethinking depending on its exact purpose.
    # In a catcode system, "immediate" often relates to expansion rather than parsing.
    # Leaving it for now but be aware it might need adjustment.
    def parse_immediate_token(self) -> ASTNode | None:
        """
        Parses an 'immediate' token. Behavior depends heavily on context in TeX.
        This is a simplified implementation.
        """
        tok = self.peek()  # TokenStream.peek handles skipping ignored
        if not tok:
            return None

        if tok.type == TokenType.CHARACTER and tok.catcode in [
            Catcode.LETTER,
            Catcode.OTHER,
        ]:
            return TextNode(tok.value)
        return self.parse_element()

    def _combine_sequence_as_str(self, predicate: Callable[[Token], bool]):
        tok = self.peek()
        out = ""
        while tok and predicate(tok):
            out += tok.value
            self.consume()
            tok = self.peek()
        return out

    def _combine_spaces(self):
        # Combine consecutive space tokens into a single TextNode
        out = self.consume().value
        out += self._combine_sequence_as_str(lambda tok: tok == WHITESPACE_TOKEN)
        return TextNode(out)

    def _combine_text(self):
        # Combine consecutive characters with catcode 11 or 12 into a TextNode.
        out = self.consume().value
        out += self._combine_sequence_as_str(is_text_token)
        return TextNode(out)

    def parse_element(self, skip_whitespace=False) -> Optional[ASTNode]:
        """
        Parses the next significant element from the token stream
        based on the current token's type and catcode.
        Returns None for tokens that are consumed but produce no AST node (like comments).
        """
        # skip_ignored is handled by peek/consume in TokenStream
        # self.skip_ignored()

        if skip_whitespace:
            self.skip_whitespace()

        tok = self.peek()  # TokenStream.peek handles skipping ignored
        if tok is None:
            return None  # End of stream

        # --- Dispatch based on Token Type and Catcode ---

        if tok.type == TokenType.CONTROL_SEQUENCE:
            # It's a command token (\section, \begin, \end, \catcode, etc.)
            # The parser's job is to recognize the *syntax* of the command and its arguments.
            # The expander will later execute the command's handler.
            return self.parse_command()  # Unified command parsing
        elif tok.type == TokenType.END_OF_LINE:
            self.consume()  # Consume the newline token (TokenStream.consume handles ignored)
            return EndOfLineNode()

        elif tok.type == TokenType.MATH_SHIFT:
            return MathShiftNode(tok.value)

        elif tok.type == TokenType.CHARACTER:
            # It's a character token with a specific catcode
            catcode = tok.catcode

            if catcode == Catcode.BEGIN_GROUP:  # { (Catcode 1)
                return self.parse_brace_group()
            elif catcode == Catcode.END_GROUP:  # } (Catcode 2)
                # This indicates a mismatched group end. Handle as error.
                print(f"ERROR: Mismatched group end '}}' at position {tok.position}")
                self.consume()  # Consume the erroneous token (TokenStream.consume handles ignored)
                return None  # Or return an error node

            elif catcode == Catcode.OTHER and tok.value == "[":
                bracket = self.parse_bracket_group()
                # if bracket, return as text([) ... text(]) in this main loop
                # if isinstance(bracket, BracketNode):
                #     return [TextNode("[")] + bracket.children + [TextNode("]")]
                return bracket
            elif catcode == Catcode.OTHER and tok.value == "]":
                # This indicates a mismatched group end. Handle as error.
                # print(f"ERROR: Mismatched group end ']' at position {tok.position}")
                self.consume()
                return TextNode(tok.value)

            elif catcode == Catcode.MATH_SHIFT:  # $ (Catcode 3)
                # The tokenizer should ideally handle full math blocks ($...$, \[...\])
                print(
                    f"WARNING: Math shift character '{tok.value}' encountered in parse_element at position {tok.position}. Assuming tokenizer handles blocks."
                )
                self.consume()  # Consume the delimiter (TokenStream.consume handles ignored)
                return MathShiftNode(tok.value)  # Or return a MathDelimiterNode

            elif catcode == Catcode.ALIGNMENT_TAB:  # & (Catcode 4)
                self.consume()  # Consume the & token (TokenStream.consume handles ignored)
                return CommandNode(
                    tok.value
                )  # Represent & as a special command-like node

            elif catcode == Catcode.PARAMETER:  # # (Catcode 6)
                return self.parse_argnode()

            elif catcode == Catcode.SPACE:  # Space, Tab (Catcode 10)
                return self._combine_spaces()

            elif catcode == Catcode.END_OF_LINE:  # Newline (Catcode 5)
                self.consume()  # Consume the newline token (TokenStream.consume handles ignored)
                # Newlines often become space tokens or \par tokens later in expansion.
                # For now, you might discard it or represent it as a special node.
                # Discarding for now.
                return None  # Or return a NewlineNode()

            elif catcode == Catcode.ACTIVE:  # ~ (Catcode 13) or other active chars
                self.consume()  # Consume the active character token (TokenStream.consume handles ignored)
                # Active characters are expandable. The expander will handle them.
                # Represent them as a CommandNode so the expander looks them up.
                return CommandNode(tok.value)  # e.g., CommandNode("~")

            elif catcode in [
                Catcode.LETTER,
                Catcode.OTHER,
            ]:
                return self._combine_text()

            # Catcodes 9 (Ignored) and 14 (Comment) are handled by TokenStream peek/consume.
            # Catcode 15 (Invalid) should ideally be handled by the tokenizer with an error token.

            else:
                # Should not reach here if all catcodes are handled
                print(
                    f"WARNING: Unhandled catcode {catcode} for character {tok.value!r} at position {tok.position} in parse_element."
                )
                self.consume()  # Consume to avoid infinite loop (TokenStream.consume handles ignored)
                return TextNode(tok.value)  # Return as text fallback

        # # Handle other potential TokenType values if your tokenizer emits them (like math blocks)
        # elif tok.type in (TokenType.MATH_INLINE, TokenType.MATH_DISPLAY):
        #     # The tokenizer already captured the math content.
        #     self.consume()  # Consume the math token (TokenStream.consume handles ignored)
        #     # The value of the token is the math content string
        #     return EquationNode(tok.value, inline=(tok.type == TokenType.MATH_INLINE))

        # Your old TokenType.BEGIN and TokenType.END are now CONTROL_SEQUENCE tokens
        # with values "begin" and "end". They are handled by parse_command.

        elif tok.type == TokenType.INVALID:
            print(
                f"ERROR: Parser encountered invalid token: {tok!r} at position {tok.position}"
            )
            self.consume()  # Consume the invalid token (TokenStream.consume handles ignored)
            return None  # Or return an ErrorNode

        else:
            # Handle any other unexpected token types
            print(
                f"WARNING: Unexpected token type {tok.type} at position {tok.position} in parse_element."
            )
            self.consume()  # Consume to avoid infinite loop (TokenStream.consume handles ignored)
            return TextNode(str(tok.value))  # Return as text fallback

    def _parse_group(self, end_token: Token, strip=False) -> List[ASTNode]:
        """Parses content within a group delimited by catcodes."""
        # Assume the opening delimiter token has already been consumed by the caller
        # (e.g., parse_brace_group consumes the '{' token)

        children: List[ASTNode] = []
        start_pos = self.stream.pos
        # Loop until the end delimiter is found or end of stream
        while not self.eof() and not self.match_token(end_token):
            # Parse the next element inside the group
            ele = self.parse_element()
            if ele:
                children.append(ele)

        # Consume the closing delimiter token
        # peek() handles skipping ignored tokens before checking
        if self.match_token(end_token):
            self.consume()  # TokenStream.consume handles skipping ignored
        else:
            # This case should ideally be caught by the loop condition, but handle defensively
            print(f"ERROR: Expected closing delimiter end_token: {end_token!r}")
            self.stream.set_pos(start_pos)
            return None

        if strip and len(children) > 0:
            # Basic stripping, might need more sophisticated logic
            if isinstance(children[0], TextNode):
                children[0].text = children[0].text.lstrip()
            if isinstance(children[-1], TextNode):
                children[-1].text = children[-1].text.rstrip()
        return children

    # parse_brace_group now uses Catcode.BEGIN_GROUP and Catcode.END_GROUP
    def parse_brace_group(self, strip=False) -> BraceNode:
        """Parses a mandatory group {...}."""
        # Consume the opening brace token (Catcode 1)
        # Use match to peek and confirm before consuming (match uses peek which handles ignored)
        if not (self.match_token(BEGIN_BRACE_TOKEN)):
            # This error should ideally be caught by parse_element dispatching here
            print(
                f"ERROR: Expected opening brace (catcode {Catcode.BEGIN_GROUP.name}), but found {self.peek()!r} at position {self.stream.pos if self.stream else -1}"
            )
            # Handle error: perhaps return an empty BraceNode or raise error
            # Attempt to consume the unexpected token to avoid infinite loop (consume handles ignored)
            self.consume()
            return BraceNode([])  # Return empty group on error

        tok = (
            self.consume()
        )  # Consume the '{' token (TokenStream.consume handles ignored)

        # Parse the content using the generic _parse_group method
        children = self._parse_group(END_BRACE_TOKEN, strip)

        if children is None:
            return TextNode(tok.value)

        return BraceNode(children)

    # parse_bracket_group now uses Catcode.OTHER for brackets (default)
    # Note: Brackets [] are NOT standard TeX group delimiters like {}
    # Their grouping behavior is often handled by the command that expects them as optional args.
    # However, if you want to parse them as structural nodes, this is how you'd do it.
    # This assumes '[' and ']' have Catcode.OTHER (12) by default.
    def parse_bracket_group(self, strip=False) -> BracketNode:
        """Parses an optional group [...]."""
        # Consume the opening bracket token (usually Catcode 12)
        # You need to check the specific character value '[' as well as catcode
        # Use match to peek and confirm before consuming (match uses peek which handles ignored)
        if not (self.match_token(BEGIN_BRACKET_TOKEN)):
            # This error should ideally be caught by parse_element dispatching here
            print(
                f"ERROR: Expected opening bracket '[' (catcode {Catcode.OTHER.name}), but found {self.peek()!r} at position {self.stream.pos_ignoring_ignored if self.stream else -1}"
            )
            # Handle error: return empty BracketNode
            # Attempt to consume the unexpected token
            self.consume()
            return BracketNode([])

        # Consume the '[' token (TokenStream.consume handles ignored)
        tok = self.consume()
        children = self._parse_group(END_BRACKET_TOKEN, strip)
        if children is None:
            return TextNode(tok.value)

        return BracketNode(children)

    # parse_command now handles CONTROL_SEQUENCE tokens
    def parse_command(self) -> CommandNode:
        """
        Parses a command invocation.
        Assumes the current token is a CONTROL_SEQUENCE token.
        """
        # Assume the current token is already identified as a CONTROL_SEQUENCE by parse_element
        cmd_tok = (
            self.consume()
        )  # Consume the command token (\foo, \begin, \end etc.) (TokenStream.consume handles ignored)

        if cmd_tok.type != TokenType.CONTROL_SEQUENCE:
            # Should not happen if parse_element dispatches correctly
            print(
                f"ERROR: parse_command called with non-command token: {cmd_tok!r} at position {cmd_tok.position}"
            )
            # Return an error node or the token as text
            return TextNode(str(cmd_tok.value))  # Fallback

        # The value of a CONTROL_SEQUENCE token is the command name *without* the backslash
        command_name = "\\" + str(
            cmd_tok.value
        )  # Re-add the backslash for the AST node name

        return CommandNode(command_name)

    # _parse_environment_name now uses catcodes for group and command tokens
    def _parse_environment_name(self) -> str | None:
        """Parse an environment name like {align} and return the name string."""
        self.skip_whitespace()  # Uses TokenStream skip_whitespace which handles ignored
        # Expecting a mandatory brace group {envname}
        # parse_brace_group uses catcodes internally and TokenStream peek/consume
        name_group = self.parse_brace_group()

        if not isinstance(name_group, BraceNode):
            # Should be a BraceNode if parsing was successful
            print(
                f"ERROR: Expected brace group for environment name, but got {type(name_group).__name__} at position {self.stream.pos_ignoring_ignored if self.stream else -1}"
            )
            return None

        # Extract the text content from the children of the BraceNode
        # The children should ideally be TextNodes or simple character nodes after expansion
        # but at the parser stage, they might be other nodes if the name was complex.
        # For simplicity, join text content.
        name_parts = []
        for child in name_group.children:
            if isinstance(child, TextNode):
                name_parts.append(child.text)
            # Add handling for other node types if they can appear in env names

        return "".join(name_parts).strip()

    # parse_environment now uses catcodes for begin/end commands and groups
    def parse_environment(
        self, begin_tok: Token = BEGIN_ENV_TOKEN, end_tok: Token = END_ENV_TOKEN
    ) -> EnvironmentNode:
        r"""
        Parses an environment block \begin{name} ... \end{name}.
        Assumes the current token is a CONTROL_SEQUENCE token for \\begin.
        """
        # Assume the current token is \begin (CONTROL_SEQUENCE, value="begin")
        start_tok = self.consume()  # TokenStream.consume handles ignored

        if start_tok != begin_tok:
            print(f"ERROR: parse_environment start_tok does not match begin_tok")
            # Handle error
            return None  # EnvironmentNode("error", [], [], [])  # Return error node

        name = self._parse_environment_name()
        if name is None:
            print(
                f"ERROR: Failed to parse environment name atposition {start_tok.position}"
            )
            # Handle error
            # Consume tokens until a likely end or brace to attempt recovery?
            # For now, return error node
            return None  # EnvironmentNode("error", [], [], [])

        # Parse optional args [...] and mandatory args {...} that follow \begin{name}
        # These are syntactically part of the \begin line.
        opt_args: List[BracketNode] = []
        mand_args: List[BraceNode] = []

        # Parse optional args (BracketNode, usually Catcode 12 for [)
        # Use match to check for the opening bracket token (match uses peek which handles ignored)
        while self.match_token(BEGIN_BRACKET_TOKEN):
            opt_args.append(self.parse_bracket_group())

        # Parse mandatory args (BraceNode, Catcode 1 for {)
        # Use match to check for the opening brace token (match uses peek which handles ignored)
        while self.match_token(BEGIN_BRACE_TOKEN):
            mand_args.append(self.parse_brace_group())

        body: List[ASTNode] = []
        end_name = None

        while end_name != name:
            tok = self.peek()
            if not tok:
                break
            while tok != end_tok:
                # ideally this is handled in expander phase
                if tok == begin_tok:
                    env_node = self.parse_environment()
                    if env_node:
                        body.append(env_node)
                else:
                    ele = self.parse_element()
                    if ele:
                        body.append(ele)
                tok = self.peek()
                if not tok:
                    break
            if tok == end_tok:
                self.consume()  # consume '\end'
                end_name = self._parse_environment_name()

        return EnvironmentNode(name, opt_args, mand_args, body)

    # parse_hash now uses catcodes for # and digits
    def parse_argnode(self) -> ASTNode:
        """
        Parses a # token, typically for macro parameters (#1, ##1, etc.).
        Assumes the current token is a CHARACTER token with catcode 6 (#).
        """
        # Assume the current token is # (CHARACTER, catcode 6)
        hash_tok = self.consume()  # TokenStream.consume handles ignored

        if not hash_tok:
            return None

        fallback_str = hash_tok.value
        if not is_param_token(hash_tok):
            print(
                f"ERROR: parse_hash called on non-# token: {hash_tok!r} at position {hash_tok.position}"
            )
            # Handle error
            return TextNode(fallback_str)  # Fallback

        # Count consecutive # characters
        hash_count = 1
        # peek() handles skipping ignored
        tok = self.peek()
        while tok and is_param_token(tok):
            fallback_str += tok.value
            self.consume()  # TokenStream.consume handles ignored
            hash_count += 1
            tok = self.peek()

        # Expect a digit (Catcode 12) or a letter (Catcode 11, for control word parameter)
        if tok and is_integer_token(tok):
            param_number = self.parse_integer()
            return ArgNode(param_number, num_params=hash_count)

        # Add handling for other cases if needed:
        # - # followed by a letter (e.g., #\commandname for \futurelet)
        # - ## followed by #1 etc. (handled by hash_count)
        # - # followed by non-digit/non-letter (error?)

        # If it's not followed by a digit, treat the # sequence as literal text for now
        # This might need refinement based on TeX rules for # outside definitions.
        print(
            f"WARNING: # sequence not followed by a digit at position {hash_tok.position}. Treating as text."
        )
        return TextNode(fallback_str)

    """HELPER FUNCTIONS"""

    def parse_integer(self) -> int:
        sequence = self._combine_sequence_as_str(is_integer_token)
        if not sequence:
            return None
        return int(sequence)

    def parse_float(self) -> float:
        sequence = self._combine_sequence_as_str(is_digit_token)
        if not sequence:
            return None
        return float(sequence)

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

    def parse_dimension_unit(self) -> str:
        start_pos = self.stream.pos
        combined_text = self._combine_sequence_as_str(
            lambda tok: tok.catcode == Catcode.LETTER
        )
        if not DimensionNode.is_valid_unit(combined_text):
            print(f"WARNING: Invalid unit: {combined_text} at position {start_pos}")
            # if not found, reset
            self.set_pos(start_pos)
            return None
        return combined_text

    def parse_dimension(self) -> DimensionNode:
        value = self.parse_float()
        if value is None:
            return None
        self.skip_whitespace()
        unit = self.parse_dimension_unit()
        if unit is None:
            return None
        return DimensionNode(value, unit)

    def parse_asterisk(self) -> bool:
        if self.match(value="*", catcode=Catcode.OTHER):
            self.consume()
            return True
        return False


# --- Example Usage for Unit Testing Parser in Isolation ---
if __name__ == "__main__":

    parser = ParserCore()

    text = r"""
    $
    """.strip()

    parser.set_text(text)
    print(parser.parse_immediate_token())
