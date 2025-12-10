from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def ifbeginwith_handler(expander: ExpanderCore, _token: Token):
    r"""
    Handler for \IfBeginWith{<string>}{<prefix>}{<true>}{<false>}
    Checks if string begins with prefix and executes appropriate branch.
    """
    expander.skip_whitespace()

    # Parse the four arguments
    blocks = expander.parse_braced_blocks(4, expand=True, check_immediate_tokens=True)
    if len(blocks) != 4:
        expander.logger.warning("\\IfBeginWith expects 4 blocks")
        return []

    string_tokens = blocks[0]
    prefix_tokens = blocks[1]
    true_branch = blocks[2]
    false_branch = blocks[3]

    # Convert tokens to strings for comparison
    string = expander.convert_tokens_to_str(string_tokens)
    prefix = expander.convert_tokens_to_str(prefix_tokens)

    # Check if string begins with prefix
    if string.startswith(prefix):
        if true_branch:
            expander.push_tokens(true_branch)
    else:
        if false_branch:
            expander.push_tokens(false_branch)

    return []


def strgobble_left_handler(expander: ExpanderCore, _token: Token):
    r"""
    Handler for \StrGobbleLeft{<string>}{<n>}
    Removes n characters from the left of the string.
    """
    expander.skip_whitespace()

    # Parse the two arguments
    blocks = expander.parse_braced_blocks(2, expand=True, check_immediate_tokens=True)
    if len(blocks) != 2:
        expander.logger.warning("\\StrGobbleLeft expects 2 blocks")
        return []

    string_tokens = blocks[0]
    count_tokens = blocks[1]

    # Convert tokens to strings
    string = expander.convert_tokens_to_str(string_tokens)
    count_str = expander.convert_tokens_to_str(count_tokens).strip()

    # Parse count as integer
    try:
        count = int(count_str)
    except ValueError:
        expander.logger.warning(f"\\StrGobbleLeft expects integer count, got '{count_str}'")
        return []

    # Remove count characters from the left
    result = string[count:] if count < len(string) else ""

    # Convert result back to tokens
    return expander.convert_str_to_tokens(result)


def strgobble_right_handler(expander: ExpanderCore, _token: Token):
    r"""
    Handler for \StrGobbleRight{<string>}{<n>}
    Removes n characters from the right of the string.
    """
    expander.skip_whitespace()

    # Parse the two arguments
    blocks = expander.parse_braced_blocks(2, expand=True, check_immediate_tokens=True)
    if len(blocks) != 2:
        expander.logger.warning("\\StrGobbleRight expects 2 blocks")
        return []

    string_tokens = blocks[0]
    count_tokens = blocks[1]

    # Convert tokens to strings
    string = expander.convert_tokens_to_str(string_tokens)
    count_str = expander.convert_tokens_to_str(count_tokens).strip()

    # Parse count as integer
    try:
        count = int(count_str)
    except ValueError:
        expander.logger.warning(f"\\StrGobbleRight expects integer count, got '{count_str}'")
        return []

    # Remove count characters from the right
    result = string[:-count] if count > 0 and count < len(string) else (string if count <= 0 else "")

    # Convert result back to tokens
    return expander.convert_str_to_tokens(result)


def ifsubstr_handler(expander: ExpanderCore, _token: Token):
    r"""
    Handler for \IfSubStr[*][<number>]{<string>}{<stringA>}{<true>}{<false>}
    Tests if string contains at least number times stringA and executes appropriate branch.
    The default value of number is 1.
    - If number <= 0, runs false
    - If string or stringA is empty, runs false
    """
    expander.skip_whitespace()

    # Check for optional star
    has_star = False
    if expander.peek() and expander.peek().value == "*":
        has_star = True
        expander.expand_next()  # consume the star
        expander.skip_whitespace()

    # Check for optional number argument
    number = 1  # default value
    number_tokens = expander.parse_bracket_as_tokens(expand=True)
    if number_tokens is not None:
        number_str = expander.convert_tokens_to_str(number_tokens).strip()
        try:
            number = int(number_str)
        except ValueError:
            expander.logger.warning(f"\\IfSubStr: invalid number argument '{number_str}', using default 1")
            number = 1
        expander.skip_whitespace()

    # Parse the four mandatory arguments
    blocks = expander.parse_braced_blocks(4, expand=True, check_immediate_tokens=True)
    if len(blocks) != 4:
        expander.logger.warning("\\IfSubStr expects 4 blocks")
        return []

    string_tokens = blocks[0]
    substring_tokens = blocks[1]
    true_branch = blocks[2]
    false_branch = blocks[3]

    # Convert tokens to strings for comparison
    string = expander.convert_tokens_to_str(string_tokens)
    substring = expander.convert_tokens_to_str(substring_tokens)

    # Determine result based on conditions
    result = False
    if number > 0 and string and substring:
        # Count occurrences of substring in string
        count = string.count(substring)
        result = count >= number

    # Execute appropriate branch
    if result:
        if true_branch:
            expander.push_tokens(true_branch)
    else:
        if false_branch:
            expander.push_tokens(false_branch)

    return []


def register_xstring_handler(expander: ExpanderCore):
    """Register all xstring package handlers."""
    expander.register_handler("IfBeginWith", ifbeginwith_handler, is_global=True)
    expander.register_handler("IfSubStr", ifsubstr_handler, is_global=True)
    expander.register_handler("StrGobbleLeft", strgobble_left_handler, is_global=True)
    expander.register_handler("StrGobbleRight", strgobble_right_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    # Test IfBeginWith
    test_ifbeginwith = r"""
    \IfBeginWith{foobar}{foo}{MATCH}{NO MATCH}
    \IfBeginWith{foobar}{bar}{MATCH}{NO MATCH}
    \IfBeginWith{hello world}{hello}{MATCH}{NO MATCH}
    \IfBeginWith{hello world}{world}{MATCH}{NO MATCH}
    """
    out = expander.expand(test_ifbeginwith)
    out_str = expander.convert_tokens_to_str(out).strip()
    print("IfBeginWith test:")
    print(out_str)
    print()

    # Test StrGobbleLeft
    test_gobbleleft = r"""
    \StrGobbleLeft{foobar}{3}
    \StrGobbleLeft{hello world}{6}
    \StrGobbleLeft{test}{10}
    """
    out = expander.expand(test_gobbleleft)
    out_str = expander.convert_tokens_to_str(out).strip()
    print("StrGobbleLeft test:")
    print(out_str)
    print()

    # Test StrGobbleRight
    test_gobbleright = r"""
    \StrGobbleRight{foobar}{3}
    \StrGobbleRight{hello world}{6}
    \StrGobbleRight{test}{10}
    """
    out = expander.expand(test_gobbleright)
    out_str = expander.convert_tokens_to_str(out).strip()
    print("StrGobbleRight test:")
    print(out_str)
    print()

    # Test combined usage
    test_combined = r"""
    \def\mystring{prefix_content_suffix}
    \IfBeginWith{\mystring}{prefix}{
        String starts with prefix: \StrGobbleLeft{\mystring}{7}
    }{
        String does not start with prefix
    }
    """
    out = expander.expand(test_combined)
    out_str = expander.convert_tokens_to_str(out).strip()
    print("Combined test:")
    print(out_str)
    print()

    # Test IfSubStr (examples from documentation)
    test_ifsubstr = r"""
    \IfSubStr{xstring}{tri}{true}{false}\par
    \IfSubStr{xstring}{a}{true}{false}\par
    \IfSubStr{a bc def }{c d}{true}{false}\par
    \IfSubStr{a bc def }{cd}{true}{false}\par
    \IfSubStr[2]{1a2a3a}{a}{true}{false}\par
    \IfSubStr[3]{1a2a3a}{a}{true}{false}\par
    \IfSubStr[4]{1a2a3a}{a}{true}{false}
    """
    out = expander.expand(test_ifsubstr)
    out_str = expander.convert_tokens_to_str(out).strip()
    print("IfSubStr test (from documentation):")
    print(out_str)
    print()
    print("Expected:")
    print("true")
    print("false")
    print("true")
    print("false")
    print("true")
    print("true")
    print("false")
