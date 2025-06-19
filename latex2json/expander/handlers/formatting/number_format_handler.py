import decimal
import re
from typing import List, Optional
from latex2json.expander.expander_core import RELAX_TOKEN, ExpanderCore
from latex2json.registers.utils import int_to_roman
from latex2json.tokens import Token
from latex2json.tokens.types import BEGIN_BRACE_TOKEN


def num_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    options = expander.parse_brace_name(bracket=True)
    expander.skip_whitespace()
    number_tokens = expander.parse_brace_as_tokens()
    if not number_tokens:
        expander.logger.warning("num: Missing number argument")
        return None

    # push \relax token in case so that parse_float does not overconsume
    expander.push_tokens(number_tokens + [RELAX_TOKEN])
    number = expander.parse_float()

    if number is None:
        return None

    tok = expander.peek()
    if tok and tok == RELAX_TOKEN:
        expander.consume()

    # Parse options
    if options and "round-precision" in options:
        precision_match = re.search(r"round-precision=(\d+)", options)
        if precision_match:
            precision = int(precision_match.group(1))
            decimal_num = decimal.Decimal(number)
            quantizer = decimal.Decimal("0." + "0" * precision)
            rounded = decimal_num.quantize(quantizer, rounding=decimal.ROUND_HALF_UP)
            number = rounded

    return expander.convert_str_to_tokens(str(number))


def romannumeral_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    tok = expander.peek()
    if tok is None:
        return None

    if tok == BEGIN_BRACE_TOKEN:
        try:
            number = int(expander.parse_brace_name())
        except ValueError:
            expander.logger.warning("romannumeral: Invalid number argument")
            return None
    else:
        number = expander.parse_integer()
    if number is None:
        expander.logger.warning("romannumeral: Missing number argument")
        return None
    if number < 0:
        # \romannumeral does not show negative numbers in latex
        return []
    return expander.convert_str_to_tokens(int_to_roman(number))


def register_number_format_handlers(expander: ExpanderCore):
    expander.register_handler("num", num_handler, is_global=True)
    expander.register_handler("romannumeral", romannumeral_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_number_format_handlers(expander)

    text = r"\num{1.234567890}"
    out = expander.expand(text)
    print(out)
