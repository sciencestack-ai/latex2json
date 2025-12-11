from latex2json.nodes.base_nodes import TextNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token, TokenType


def symbol_handler(parser: ParserCore, token: Token):
    r"""
    Handle the \symbol{<number>} command.

    Supports three number formats:
    - Hexadecimal: \symbol{"E052} or \symbol{0xE052}
    - Octal: \symbol{'162402}
    - Decimal: \symbol{58626}

    Args:
        parser: The parser instance
        token: The \symbol command token

    Returns:
        List containing a TextNode with the Unicode character
    """
    parser.skip_whitespace()
    tok = parser.peek()

    if not tok or tok != BEGIN_BRACE_TOKEN:
        return []

    parser.consume()  # consume opening brace

    # Collect all tokens until closing brace
    number_tokens = []
    tok = parser.peek()

    while tok and tok != END_BRACE_TOKEN:
        if tok.type == TokenType.CHARACTER:
            number_tokens.append(tok.value)
            parser.consume()
            tok = parser.peek()
        else:
            # Unexpected token type
            parser.consume()
            tok = parser.peek()

    if tok == END_BRACE_TOKEN:
        parser.consume()  # consume closing brace

    if not number_tokens:
        return []

    # Join the tokens to get the number string
    number_str = "".join(number_tokens).strip()

    if not number_str:
        return []

    # Parse the number based on prefix
    try:
        codepoint = None

        # Hexadecimal with " prefix (TeX-style)
        if number_str.startswith('"'):
            codepoint = int(number_str[1:], 16)
        # Hexadecimal with 0x prefix
        elif number_str.startswith('0x') or number_str.startswith('0X'):
            codepoint = int(number_str, 16)
        # Octal with ' prefix (TeX-style)
        elif number_str.startswith("'"):
            codepoint = int(number_str[1:], 8)
        # Decimal (default)
        else:
            codepoint = int(number_str, 10)

        # Convert codepoint to character
        if codepoint is not None and 0 <= codepoint <= 0x10FFFF:
            char = chr(codepoint)
            return [TextNode(char)]
    except (ValueError, OverflowError):
        # Invalid number format
        pass

    return []


def usym_handler(parser: ParserCore, token: Token):
    r"""
    Handle the \usym{<hex>} command from the utfsym package.

    Takes a hexadecimal Unicode codepoint without prefix.
    Example: \usym{1F642} for U+1F642

    Args:
        parser: The parser instance
        token: The \usym command token

    Returns:
        List containing a TextNode with the Unicode character
    """
    parser.skip_whitespace()
    tok = parser.peek()

    if not tok or tok != BEGIN_BRACE_TOKEN:
        return []

    parser.consume()  # consume opening brace

    # Collect all tokens until closing brace
    hex_tokens = []
    tok = parser.peek()

    while tok and tok != END_BRACE_TOKEN:
        if tok.type == TokenType.CHARACTER:
            hex_tokens.append(tok.value)
            parser.consume()
            tok = parser.peek()
        else:
            parser.consume()
            tok = parser.peek()

    if tok == END_BRACE_TOKEN:
        parser.consume()  # consume closing brace

    if not hex_tokens:
        return []

    # Join the tokens to get the hex string
    hex_str = "".join(hex_tokens).strip()

    if not hex_str:
        return []

    # Parse as hexadecimal (no prefix needed)
    try:
        codepoint = int(hex_str, 16)

        # Convert codepoint to character
        if 0 <= codepoint <= 0x10FFFF:
            char = chr(codepoint)
            return [TextNode(char)]
    except (ValueError, OverflowError):
        # Invalid hex format
        pass

    return []


def char_handler(parser: ParserCore, token: Token):
    r"""
    Handle the \char<number> primitive.

    Like \symbol but doesn't use braces - reads the number directly.
    Supports three number formats:
    - Hexadecimal: \char"E052 (TeX-style with " prefix)
    - Octal: \char'101 (TeX-style with ' prefix)
    - Decimal: \char65

    Args:
        parser: The parser instance
        token: The \char command token

    Returns:
        List containing a TextNode with the Unicode character
    """
    parser.skip_whitespace()

    # Peek at the next token to determine format
    tok = parser.peek()
    if not tok or tok.type != TokenType.CHARACTER:
        return []

    # Collect number tokens
    number_chars = []
    first_char = tok.value

    # Check for prefix
    if first_char == '"':
        # Hexadecimal with " prefix
        parser.consume()  # consume the "
        tok = parser.peek()
        while tok and tok.type == TokenType.CHARACTER and tok.value.lower() in '0123456789abcdef':
            number_chars.append(tok.value)
            parser.consume()
            tok = parser.peek()

        if number_chars:
            try:
                codepoint = int(''.join(number_chars), 16)
                if 0 <= codepoint <= 0x10FFFF:
                    return [TextNode(chr(codepoint))]
            except (ValueError, OverflowError):
                pass

    elif first_char == "'":
        # Octal with ' prefix
        parser.consume()  # consume the '
        tok = parser.peek()
        while tok and tok.type == TokenType.CHARACTER and tok.value in '01234567':
            number_chars.append(tok.value)
            parser.consume()
            tok = parser.peek()

        if number_chars:
            try:
                codepoint = int(''.join(number_chars), 8)
                if 0 <= codepoint <= 0x10FFFF:
                    return [TextNode(chr(codepoint))]
            except (ValueError, OverflowError):
                pass

    else:
        # Decimal (default)
        while tok and tok.type == TokenType.CHARACTER and tok.value.isdigit():
            number_chars.append(tok.value)
            parser.consume()
            tok = parser.peek()

        if number_chars:
            try:
                codepoint = int(''.join(number_chars), 10)
                if 0 <= codepoint <= 0x10FFFF:
                    return [TextNode(chr(codepoint))]
            except (ValueError, OverflowError):
                pass

    return []


def register_symbol_handler(parser: ParserCore):
    r"""Register the \symbol, \usym, and \char command handlers."""
    parser.register_handler("symbol", symbol_handler)
    parser.register_handler("usym", usym_handler)
    parser.register_handler("char", char_handler)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()

    # Test cases
    test_strings = [
        r'\symbol{"E052}',  # Hex with " prefix
        r'\symbol{0xE052}',  # Hex with 0x prefix
        r"\symbol{'162402}",  # Octal with ' prefix
        r'\symbol{58626}',  # Decimal
        r'\symbol{"0041}',  # 'A' in hex
        r'\symbol{65}',  # 'A' in decimal
        r'\symbol{"03B1}',  # Greek alpha
    ]

    for text in test_strings:
        out = parser.parse(text)
        print(f"{text} -> {out}")
