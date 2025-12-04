import re
import math
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import Token
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.utils import convert_str_to_tokens


class PGFMathEvaluator:
    """Evaluates PGF mathematical expressions and stores results."""

    def __init__(self):
        self.result = "0"  # Default result

    def parse_and_evaluate(self, expr_str: str) -> str:
        """
        Parse and evaluate a PGF math expression.
        Returns the result as a string.
        """
        try:
            # Clean up the expression
            expr = expr_str.strip()

            # Convert PGF math syntax to Python syntax
            expr = self._convert_pgf_to_python(expr)

            # Create a safe evaluation context with math functions
            safe_dict = {
                "__builtins__": {},
                "abs": abs,
                "min": min,
                "max": max,
                "pow": pow,
                "round": round,
                # Math module functions
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "asin": math.asin,
                "acos": math.acos,
                "atan": math.atan,
                "sinh": math.sinh,
                "cosh": math.cosh,
                "tanh": math.tanh,
                "sqrt": math.sqrt,
                "exp": math.exp,
                "ln": math.log,
                "log": math.log10,
                "floor": math.floor,
                "ceil": math.ceil,
                "pi": math.pi,
                "e": math.e,
            }

            # Evaluate the expression
            result = eval(expr, safe_dict)

            # Format the result
            if isinstance(result, bool):
                return "1" if result else "0"
            elif isinstance(result, (int, float)):
                # Keep reasonable precision
                if isinstance(result, float):
                    # Remove trailing zeros and unnecessary decimal point
                    formatted = f"{result:.10f}".rstrip("0").rstrip(".")
                    return formatted
                return str(result)
            else:
                return str(result)

        except Exception:
            # Return 0 on error (PGF's default behavior)
            return "0"

    def _convert_pgf_to_python(self, expr: str) -> str:
        """Convert PGF math syntax to Python syntax."""
        # Replace PGF operators with Python equivalents
        expr = expr.replace("^", "**")  # Exponentiation

        # Handle comparison operators (PGF returns 1.0 or 0.0)
        expr = re.sub(r"==", "==", expr)
        expr = re.sub(r"!=", "!=", expr)

        # Handle logical operators
        expr = expr.replace("&&", " and ")
        expr = expr.replace("||", " or ")
        expr = expr.replace("!", " not ")

        # Handle ternary operator: condition ? true_val : false_val
        # Convert to Python: true_val if condition else false_val
        ternary_pattern = r"\(([^?:]+)\?([^:]+):([^)]+)\)"
        expr = re.sub(
            ternary_pattern,
            lambda m: f"({m.group(2)} if {m.group(1)} else {m.group(3)})",
            expr,
        )

        # Handle modulo operator
        expr = re.sub(r"\bmod\b", "%", expr)

        # Remove 'pt' units (common in PGF)
        expr = re.sub(r"(\d+(?:\.\d+)?)\s*pt", r"\1", expr)

        # Handle degrees to radians conversion for trig functions
        # PGF uses degrees by default
        expr = re.sub(r"\bsin\(([^)]+)\)", r"sin((\1)*pi/180)", expr)
        expr = re.sub(r"\bcos\(([^)]+)\)", r"cos((\1)*pi/180)", expr)
        expr = re.sub(r"\btan\(([^)]+)\)", r"tan((\1)*pi/180)", expr)

        return expr


def register_pgfmath(expander: ExpanderCore):
    """Register PGF math handlers."""
    # Create a single evaluator instance shared across all handlers
    evaluator = PGFMathEvaluator()

    def pgfmathparse_handler(expander: ExpanderCore, _token: Token):
        r"""
        Handler for \pgfmathparse{expression}
        Evaluates the mathematical expression and stores the result.
        """
        expander.skip_whitespace()
        expr_tokens = expander.parse_brace_as_tokens(expand=True)

        if not expr_tokens:
            return []

        # Convert tokens to string
        expr_str = expander.convert_tokens_to_str(expr_tokens).strip()

        # Evaluate the expression
        result = evaluator.parse_and_evaluate(expr_str)

        # Store the result
        evaluator.result = result

        # Return empty list (result is accessed via \pgfmathresult)
        return []

    def pgfmathresult_handler(expander: ExpanderCore, _token: Token):
        r"""
        Handler for \pgfmathresult
        Returns the result of the last \pgfmathparse evaluation.
        """
        result_str = evaluator.result

        # Convert result to tokens
        result_tokens = convert_str_to_tokens(result_str, catcode=Catcode.OTHER)

        return result_tokens

    def pgfmathsetmacro_handler(expander: ExpanderCore, _token: Token):
        r"""
        Handler for \pgfmathsetmacro{\macro}{expression}
        Defines \macro to expand to the result of evaluating expression.
        """
        expander.skip_whitespace()
        macro_token = expander.parse_command_name_token()

        if not macro_token:
            return []

        expander.skip_whitespace()
        expr_tokens = expander.parse_brace_as_tokens(expand=True)

        if not expr_tokens:
            return []

        # Convert tokens to string
        expr_str = expander.convert_tokens_to_str(expr_tokens).strip()

        # Evaluate the expression
        result = evaluator.parse_and_evaluate(expr_str)

        # Define the macro to expand to the result
        result_tokens = convert_str_to_tokens(result, catcode=Catcode.OTHER)
        macro = Macro(
            name=macro_token.value,
            definition=result_tokens,
            num_args=0,
            is_user_defined=True,
        )
        expander.register_macro(macro_token.value, macro, is_global=False)

        return []

    expander.register_handler("pgfmathparse", pgfmathparse_handler, is_global=True)
    expander.register_handler("pgfmathresult", pgfmathresult_handler, is_global=True)
    expander.register_handler(
        "pgfmathsetmacro", pgfmathsetmacro_handler, is_global=True
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    # Test basic arithmetic
    test1 = r"""
    \pgfmathparse{2+3*4}
    Result: \pgfmathresult
    """.strip()
    out1 = expander.expand(test1)
    print("Test 1 - Basic arithmetic:")
    print(expander.convert_tokens_to_str(out1).strip())
    print()

    # Test pgfmathsetmacro
    test2 = r"""
    \pgfmathsetmacro{\myvalue}{10*5+7}
    The value is \myvalue
    """.strip()
    out2 = expander.expand(test2)
    print("Test 2 - pgfmathsetmacro:")
    print(expander.convert_tokens_to_str(out2).strip())
    print()

    # Test with trig functions
    test3 = r"""
    \pgfmathparse{sin(30)+cos(60)}
    Trig result: \pgfmathresult
    """.strip()
    out3 = expander.expand(test3)
    print("Test 3 - Trigonometric functions:")
    print(expander.convert_tokens_to_str(out3).strip())
    print()

    # Test with power and sqrt
    test4 = r"""
    \pgfmathparse{2^3 + sqrt(16)}
    Power result: \pgfmathresult
    """.strip()
    out4 = expander.expand(test4)
    print("Test 4 - Power and sqrt:")
    print(expander.convert_tokens_to_str(out4).strip())
    print()
