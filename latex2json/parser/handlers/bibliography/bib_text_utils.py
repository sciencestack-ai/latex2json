from typing import Tuple


def count_preceding_backslashes(text: str, pos: int) -> int:
    """Count number of backslashes immediately preceding the position."""
    count = 0
    pos -= 1
    while pos >= 0 and text[pos] == "\\":
        count += 1
        pos -= 1
    return count


def is_escaped(pos: int, text: str) -> bool:
    """Check if character at position is escaped by backslashes."""
    return count_preceding_backslashes(text, pos) % 2 == 1


def find_matching_delimiter(
    text: str, open_delim: str = "{", close_delim: str = "}", start: int = 0
) -> Tuple[int, int]:
    """
    Find the position of the matching closing delimiter, handling nested delimiters.
    Returns a tuple of (start_pos, end_pos) where:
        - start_pos is the position of the opening delimiter
        - end_pos is the position after the matching closing delimiter
    Returns (-1, -1) if no valid delimiters found.
    Handles:
        - Nested delimiters
        - Escaped characters (odd number of backslashes)
    """
    # Skip leading whitespace
    while start < len(text) and text[start].isspace():
        start += 1

    if start >= len(text) or text[start] != open_delim:
        return -1, -1

    stack = []
    i = start
    while i < len(text):
        if text[i] == open_delim and not is_escaped(i, text):
            stack.append(i)
        elif text[i] == close_delim and not is_escaped(i, text):
            if not stack:
                return -1, -1  # Unmatched closing delimiter
            stack.pop()
            if not stack:  # Found the matching delimiter
                return start, i + 1
        i += 1

    return -1, -1  # No matching delimiter found


def extract_nested_content(
    text: str, open_delim: str = "{", close_delim: str = "}"
) -> Tuple[str | None, int]:
    """
    Extract content between delimiters, handling nesting.
    Returns a tuple of (content, next_position) where:
        - content is the text between delimiters (or None if not found)
        - next_position is the position after the closing delimiter (or 0 if not found)
    """
    start_pos, end_pos = find_matching_delimiter(text, open_delim, close_delim)
    if start_pos == -1:
        return None, 0

    # Return content without the delimiters and the next position to process
    content = text[start_pos + 1 : end_pos - 1]
    return content, end_pos
