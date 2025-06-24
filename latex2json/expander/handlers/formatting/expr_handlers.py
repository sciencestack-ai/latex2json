from enum import Enum
from typing import Callable, List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Handler
from latex2json.tokens import Token
from latex2json.tokens.types import TokenType


class ExprType(Enum):
    NUM = "numexpr"
    DIM = "dimexpr"
    GLUE = "glueexpr"
    MU = "muexpr"

    def __str__(self):
        return self.value


def make_expr_handler(expr_type: ExprType) -> Handler:

    def expr_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        expr_str = ""
        needs_float = True
        while not expander.eof():
            expander.skip_whitespace()
            tok = expander.peek()
            if expander.is_relax_token(tok) or tok.type == TokenType.END_OF_LINE:
                expander.consume()
                break

            if tok.value in ["(", ")"]:
                expander.consume()
                expr_str += tok.value
                continue

            if needs_float:
                out = None
                if expr_type == ExprType.NUM:
                    out = expander._parse_float()
                elif expr_type == ExprType.DIM:
                    out = expander._parse_dimensions()
                elif expr_type == ExprType.GLUE:
                    out = expander._parse_skip()
                elif expr_type == ExprType.MU:
                    out = expander._parse_skip()
                if out is None:
                    break
                val, relax = out
                if val is None:
                    break
                expr_str += str(val)
                if relax:
                    break
                needs_float = False
            else:
                if tok.value in ["+", "-", "*", "/", "^"]:
                    expander.consume()
                    expr_str += tok.value
                    needs_float = True
                    continue
                break

        if expr_str:
            # Balance parentheses - add closing brackets to match open ones
            open_count = expr_str.count("(")
            close_count = expr_str.count(")")
            if open_count > close_count:
                expr_str += ")" * (open_count - close_count)

            try:

                number = eval(expr_str)
            except Exception:
                expander.logger.warning(f"{expr_type}: Invalid expression: {expr_str}")
                return None

            if isinstance(number, (float, int)):
                number_tokens = expander.convert_str_to_tokens("%d" % (number))  # int
                return number_tokens
            else:
                expander.logger.warning(f"{expr_type}: Invalid expression: {expr_str}")
                return None
        return []

    return expr_handler


def register_expr_handlers(expander: ExpanderCore):
    expander.register_handler(
        "numexpr", make_expr_handler(ExprType.NUM), is_global=True
    )
    expander.register_handler(
        "dimexpr", make_expr_handler(ExprType.DIM), is_global=True
    )
    expander.register_handler(
        "glueexpr", make_expr_handler(ExprType.GLUE), is_global=True
    )
    expander.register_handler("muexpr", make_expr_handler(ExprType.MU), is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_expr_handlers(expander)

    text = r"""
    \setbox0=\hbox{1pt}
    \setbox1=\hbox{1pt}
    \wd0=15pt
    \wd1=10pt
    \the\dimexpr \wd0 + \wd1 \relax
    """.strip()
    out = expander.expand(text)
    print(out)
