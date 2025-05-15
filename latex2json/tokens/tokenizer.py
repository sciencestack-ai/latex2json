from typing import List, Dict, Tuple, Optional, Any
import enum

# Assume catcodes.py is in the same directory or accessible in your package
# If in a package, use from .catcodes import Catcode, DEFAULT_CATCODES
from latex2json.tokens.catcodes import (
    Catcode,
    get_default_catcodes,
)  # Example import if in same directory

from latex2json.tokens.types import Token, TokenType


# --- Implement the Catcode-Aware Tokenizer ---
class Tokenizer:
    def __init__(self, catcodes: Optional[Dict[int, Catcode]] = None) -> None:
        """
        Initializes the CatcodeTokenizer.
        Optionally accepts a catcode dictionary (mapping int char_code to Catcode enum).
        """
        # The catcode table used by this tokenizer instance
        # Stores mapping from integer character code to Catcode enum member
        self._catcodes: Dict[int, Catcode] = (
            catcodes if catcodes is not None else get_default_catcodes()
        )
        self.text = ""
        self.position = 0  # Current reading position

    @property
    def pos(self) -> int:
        return self.position

    @pos.setter
    def pos(self, value: int):
        self.position = max(0, min(len(self.text), value))

    def set_catcode(self, char_code: int, catcode: Catcode) -> None:
        """Allows changing a character's catcode dynamically."""
        self._catcodes[char_code] = catcode

    def set_catcode_table(self, catcodes: Dict[int, Catcode]) -> None:
        self._catcodes = catcodes

    def get_catcode(self, char_code: int) -> Catcode:
        """Gets the current catcode for a character code, defaulting to OTHER if unknown."""
        # Default to Catcode.OTHER if character code is not explicitly in the table
        return self._catcodes.get(char_code, Catcode.OTHER)

    def set(self, text: str):
        """Resets the tokenizer with new input text."""
        self.text = text
        self.position = 0
        # Note: Catcodes are NOT reset here. They are stateful and persist
        # unless explicitly set back to defaults or changed by \catcode.

    def eof(self) -> bool:
        """Checks if the tokenizer has reached the end of the input text."""
        return self.position >= len(self.text)

    def tokenize(self, text: str) -> List[Token]:
        """Tokenizes the input text and returns a list of tokens."""
        self.set(text)
        tokens = []
        while not self.eof():
            token = self.get_next_token()
            if token:
                tokens.append(token)

        return tokens

    def _get_catcode_sequence(self, start: int, catcode: Catcode) -> str:
        """
        Returns a sequence of characters from the current position
        that have the specified catcode.
        """
        text = self.text
        N = len(text)
        pos = start
        while pos < N:
            char_code = ord(text[pos])
            catcode = self.get_catcode(char_code)
            if catcode == Catcode.LETTER:  # Continue consuming letters
                pos += 1
            else:
                break  # Stop at the first non-letter
        command_name = text[start:pos]
        return command_name, pos

    def get_next_token(self) -> Optional[Token]:
        """
        Reads characters from the raw input and returns the next token
        based on current catcodes. Advances self.position.
        Returns None at end of input. This is the core token-emitting method.
        """
        if self.eof():
            return None

        # print(f"DEBUG: get_next_token called. Current position: {self.position}/{self.length}") # Added debug print
        text = self.text
        N = len(text)

        # Skip ignored characters (Catcode 9)
        while self.position < N:
            char_code = ord(text[self.position])
            if self.get_catcode(char_code) == Catcode.IGNORED:
                self.position += 1
            else:
                break

        # print(f"DEBUG: After skipping ignored. Position: {self.position}/{self.length}") # Added debug print

        if self.position >= N:
            # print("DEBUG: Reached end of input.") # Added debug print
            return None  # End of input

        current_char = text[self.position]
        current_char_code = ord(current_char)
        current_catcode = self.get_catcode(current_char_code)
        start_pos = self.position

        # --- Dispatch based on Catcode ---

        if current_catcode == Catcode.COMMENT:  # Comment (%)
            # Consume the comment and then CONTINUE the loop to find the next token
            self._consume_comment()
            return (
                self.get_next_token()
            )  # Recursively call to get the next non-comment token

        elif current_catcode == Catcode.SPACE:  # Space (or Tab)
            # Consume consecutive spaces and return a single space token (Catcode 10)
            # TeX typically collapses multiple spaces to one token, but the tokenizer
            # emits individual space tokens. The collapsing happens later.
            # Let's emit individual space tokens for simplicity.
            self.position += 1
            return Token(
                TokenType.CHARACTER, current_char, start_pos, catcode=Catcode.SPACE
            )

        elif (
            current_catcode == Catcode.ESCAPE
        ):  # Escape (\) - Starts a control sequence
            self.position += 1  # Consume the backslash
            if self.position >= N:
                # Handle error: backslash at end of file
                print(f"ERROR: Backslash at end of input at position {start_pos}")
                # Return an error token or None
                return None  # Or return Token(TokenType.INVALID, "\\", start_pos)

            next_char = text[self.position]
            next_char_code = ord(next_char)
            next_catcode = self.get_catcode(next_char_code)

            if (
                next_catcode == Catcode.LETTER
            ):  # Letter (Catcode 11) - Forms a control word
                command_name, pos = self._get_catcode_sequence(
                    self.position, Catcode.LETTER
                )
                self.position = pos
                return Token(TokenType.CONTROL_SEQUENCE, command_name, start_pos)
            elif next_catcode == Catcode.IGNORED:
                # break if next is an ignored char
                self.position += 1
                return Token(TokenType.CONTROL_SEQUENCE, "", start_pos)

            elif (
                next_catcode != Catcode.END_OF_LINE
            ):  # Not End of Line (Catcode 5) - Forms a control symbol (\#,\$, etc.)
                # This also handles escaped special characters like \{, \}, \\ etc.
                command_name = (
                    next_char  # The command name is just the single character
                )
                self.position += 1  # Consume the character after backslash
                return Token(TokenType.CONTROL_SEQUENCE, command_name, start_pos)

            else:  # Catcode 5 (End of Line) after backslash - becomes a space token (\ )
                # This is a simplified handling; TeX's \newline or \par from \\ is more complex
                # For now, treat as a space token
                self.position += 1  # Consume the newline
                return Token(
                    TokenType.CHARACTER, " ", start_pos, catcode=Catcode.SPACE
                )  # A space token

        # --- Handle other special catcodes that form single-character tokens ---
        # These characters become tokens representing themselves, with their catcode.
        elif current_catcode == Catcode.MATH_SHIFT:
            self.position += 1
            return Token(TokenType.MATH_SHIFT, current_char, start_pos)

        elif current_catcode in [
            Catcode.BEGIN_GROUP,
            Catcode.END_GROUP,
            Catcode.ALIGNMENT_TAB,
            Catcode.PARAMETER,
            Catcode.SUPERSCRIPT,
            Catcode.SUBSCRIPT,
            Catcode.ACTIVE,
        ]:
            self.position += 1
            return Token(
                TokenType.CHARACTER, current_char, start_pos, catcode=current_catcode
            )

        # --- Handle Catcode 5 (End of Line) ---
        # Newlines are typically converted to space tokens or \par tokens later.
        # For now, tokenize as a character token with catcode 5.
        elif current_catcode == Catcode.END_OF_LINE:
            self.position += 1
            return Token(TokenType.END_OF_LINE, current_char, start_pos)

        # --- Handle Catcode 12 (Other) and 11 (Letter) that are NOT part of commands ---
        # These form character tokens representing themselves.
        elif current_catcode in [Catcode.LETTER, Catcode.OTHER]:
            # Consume a run of consecutive characters with the same catcode (11 or 12)
            # and return them as individual CHARACTER tokens. The parser will combine
            # consecutive CHARACTER tokens with catcode 11 or 12 into TextNodes.
            self.position += 1
            return Token(
                TokenType.CHARACTER, current_char, start_pos, catcode=current_catcode
            )

        elif current_catcode == Catcode.INVALID:  # Invalid
            print(f"ERROR: Invalid character at position {start_pos}: {current_char!r}")
            self.position += 1  # Consume and report error
            # Return an error token or None
            return Token(
                TokenType.INVALID, current_char, start_pos
            )  # Return invalid token

        else:
            self.position += 1  # Consume and move on
            return Token(
                TokenType.INVALID, current_char, start_pos
            )  # Return invalid token fallback

    def _consume_comment(self) -> None:
        """Consumes characters with Catcode 14 (%) until End of Line (Catcode 5)."""
        # Assumes the current position is at the '%' character (Catcode 14)
        self.position += 1  # Consume the '%'

        while self.position < len(self.text):
            char_code = ord(self.text[self.position])
            catcode = self.get_catcode(char_code)
            if catcode != Catcode.END_OF_LINE:  # Consume until End of Line
                self.position += 1
            else:
                # Stop before consuming the End of Line character,
                # which will be tokenized in the main get_next_token loop.
                break


# --- Example Usage (Simulating Stream Processing) ---
if __name__ == "__main__":
    # Simulate the input stream and dynamic catcode changes
    input_text = r"""
    \section{First} % A comment
    Hello world!
    \makeatletter
    @@@@@
    \makeatother
    @@
    """

    input_text = r"""
$
    """.strip()
    tokenizer = Tokenizer()
    tokenizer.set(input_text)
    tokenizer.set_catcode(ord("$"), Catcode.LETTER)
    tokens = tokenizer.tokenize(input_text)
    for token in tokens:
        print(token)

    # input_text = r"""
    # -123.2 asdas \# ss
    # """.strip()

    # # Initialize the tokenizer with default catcodes
    # tokenizer = Tokenizer(catcodes=DEFAULT_CATCODES.copy())
    # tokenizer.set(input_text)  # Ensure the tokenizer is reset with the text

    # print("--- Tokenizing Input Stream ---")

    # # Simulate the main loop pulling tokens one by one
    # # In a real system, the Parser would call get_next_token()
    # token = tokenizer.get_next_token()
    # while token is not None:
    #     print(token)

    #     # Simulate the Expander executing \makeatletter and \makeatother
    #     # In a real system, this logic would be in the Expander's handlers
    #     if token.type == TokenType.CONTROL_SEQUENCE and token.value == "makeatletter":
    #         print("\n--- Simulating Expander executing \\makeatletter ---")
    #         tokenizer.set_catcode(ord("@"), Catcode.LETTER)
    #         print("--- Catcode of '@' changed to LETTER (11) ---")
    #         print("--- Continuing tokenization with new catcode ---")

    #     elif token.type == TokenType.CONTROL_SEQUENCE and token.value == "makeatother":
    #         print("\n--- Simulating Expander executing \\makeatother ---")
    #         tokenizer.set_catcode(ord("@"), Catcode.OTHER)
    #         print("--- Catcode of '@' changed back to OTHER (12) ---")
    #         print("--- Continuing tokenization with new catcode ---")

    #     # Get the next token from the stream
    #     token = tokenizer.get_next_token()

    # print("\n--- End of Token Stream ---")
