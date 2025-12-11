from typing import List, Optional, Tuple
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens import Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens, is_comma_token


def parse_multido_variable_spec(
    expander: ExpanderCore, spec_tokens: List[Token]
) -> Optional[Tuple[Token, float, float]]:
    r"""
    Parse a multido variable specification like \I=1+1 or \n=0.5+0.1
    Returns (variable_token, start_value, increment) or None if invalid
    """
    spec_str = expander.convert_tokens_to_str(spec_tokens).strip()

    # Find the variable token (should be first control sequence)
    variable_token = None
    for tok in spec_tokens:
        if tok.type == TokenType.CONTROL_SEQUENCE:
            variable_token = tok
            break

    if not variable_token:
        return None

    # Parse the value specification: var=start+increment
    if "=" not in spec_str:
        return None

    parts = spec_str.split("=", 1)
    if len(parts) != 2:
        return None

    value_part = parts[1].strip()

    # Split by + or - for increment
    if "+" in value_part:
        value_parts = value_part.split("+", 1)
        try:
            start_value = float(value_parts[0].strip())
            increment = float(value_parts[1].strip())
        except (ValueError, IndexError):
            return None
    elif "-" in value_part:
        # Handle negative increment like 10-1, 5-1, or -10-1
        # Find the last occurrence of - that's not at the start
        # and not part of a negative number after +
        idx = -1
        for i in range(len(value_part) - 1, 0, -1):
            if value_part[i] == "-":
                # Check if this is an operator minus (has a digit before it)
                if i > 0 and value_part[i - 1].replace(".", "").isdigit():
                    idx = i
                    break

        if idx > 0:
            try:
                start_value = float(value_part[:idx].strip())
                increment = -float(value_part[idx + 1 :].strip())
            except (ValueError, IndexError):
                return None
        else:
            # Just a negative start value, no increment specified
            try:
                start_value = float(value_part.strip())
                increment = 1.0
            except ValueError:
                return None
    else:
        # No increment specified, assume 1
        try:
            start_value = float(value_part.strip())
            increment = 1.0
        except ValueError:
            return None

    return (variable_token, start_value, increment)


def multido_handler(expander: ExpanderCore, token: Token):
    r"""
    Handles \multido command from the multido package.

    Syntax: \multido{\variable=start+increment}{repetitions}{body}

    Example:
        \multido{\I=1+1}{6}{%
            Item \I
        }

    This iterates 6 times with \I taking values 1, 2, 3, 4, 5, 6.

    Supports:
    - Integer variables: \I=1+1
    - Decimal variables: \n=0.0+0.5
    - Negative increments: \I=10-1 (decrement by 1)
    - Multiple variables: \multido{\I=1+1,\n=0.0+0.1}{5}{...}
    """
    # Parse the three required blocks
    blocks = expander.parse_braced_blocks(3)
    if len(blocks) != 3:
        expander.logger.warning("\\multido expects 3 blocks: {vars}{count}{body}")
        return None

    var_spec_tokens = blocks[0]
    count_tokens = expander.expand_tokens(blocks[1])
    body_tokens = blocks[2]

    # Parse repetition count
    count_str = expander.convert_tokens_to_str(count_tokens).strip()
    try:
        repetitions = int(count_str)
    except ValueError:
        expander.logger.warning(
            f"\\multido expects integer repetition count, got {count_str}"
        )
        return None

    if repetitions <= 0:
        return []

    # Parse variable specifications (can be comma-separated for multiple vars)
    # Split by comma to handle multiple variables like \I=1+1,\n=0.0+0.1
    var_specs = []
    current_spec = []

    for tok in var_spec_tokens:
        if is_comma_token(tok):
            if current_spec:
                var_specs.append(current_spec)
                current_spec = []
        else:
            current_spec.append(tok)

    if current_spec:
        var_specs.append(current_spec)

    # Parse each variable specification
    parsed_vars = []
    for spec in var_specs:
        spec = strip_whitespace_tokens(spec)
        if not spec:
            continue
        parsed = parse_multido_variable_spec(expander, spec)
        if parsed is None:
            expander.logger.warning(
                f"\\multido: invalid variable spec: "
                f"{expander.convert_tokens_to_str(spec)}"
            )
            continue
        parsed_vars.append(parsed)

    if not parsed_vars:
        expander.logger.warning("\\multido: no valid variable specifications found")
        return []

    # Execute the loop
    expander.push_scope()  # Create local scope for loop variables
    result_tokens: List[Token] = []

    for iteration in range(repetitions):
        # Update all loop variables
        for variable_token, start_value, increment in parsed_vars:
            current_value = start_value + iteration * increment

            # Format the value (as integer if whole number, otherwise as float)
            # Round to avoid floating point precision issues
            if abs(current_value - round(current_value)) < 1e-10:
                value_str = str(int(round(current_value)))
            else:
                # Round to reasonable precision to avoid floating point artifacts
                value_str = f"{current_value:.10g}"

            # Define the variable as a macro that expands to the current value
            value_tokens = expander.convert_str_to_tokens(value_str)
            expander.register_handler(
                variable_token, lambda exp, tok, v=value_tokens: v.copy(), is_global=False
            )

        # Expand the body with current variable values
        result_tokens.extend(expander.expand_tokens(body_tokens))

    expander.pop_scope()  # Clean up local variables

    return result_tokens


def register_multido_handler(expander: ExpanderCore):
    expander.register_handler("multido", multido_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    # Test basic integer variable
    text1 = r"""
\multido{\I=1+1}{6}{%
    Item \I,
}
"""

    # Test with decimal variable
    text2 = r"""
\multido{\n=0.0+0.5}{5}{%
    Value: \n
}
"""

    # Test with multiple variables
    text3 = r"""
\multido{\I=1+1,\n=0.0+0.2}{5}{%
    \I: \n
}
"""

    expander = Expander()
    register_multido_handler(expander)

    print("Test 1 (integer):")
    print(expander.expand(text1))
    print("\nTest 2 (decimal):")
    print(expander.expand(text2))
    print("\nTest 3 (multiple vars):")
    print(expander.expand(text3))
