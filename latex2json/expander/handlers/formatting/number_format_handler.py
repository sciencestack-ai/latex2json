import decimal
import re
from typing import List, Optional
from latex2json.expander.expander_core import RELAX_TOKEN, ExpanderCore
from latex2json.expander.macro_registry import Handler
from latex2json.registers.utils import int_to_roman
from latex2json.tokens import Token
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, TokenType
from latex2json.tokens.utils import (
    convert_str_to_default_token_catcodes,
    wrap_tokens_in_braces,
)


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


def number_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    val = expander.parse_integer() or 0
    return expander.convert_str_to_tokens(str(val))


def mathchoice_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    # parse 4 arguments
    blocks = expander.parse_braced_blocks(N_blocks=4, expand=False)
    if len(blocks) != 4:
        expander.logger.warning("\\mathchoice: requires 4 blocks, got %d", len(blocks))
        return None
    # pick first block arbitarily
    expander.push_tokens(blocks[0])
    return []


def qopname_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""
    \qopname\newmcodes@o{div}
    """
    toks1 = expander.parse_immediate_token(
        expand=True, skip_whitespace=True
    )  # usually \newmcodes@ or \relax
    limit_tok = expander.parse_immediate_token(expand=True, skip_whitespace=True)
    if not limit_tok:
        return None
    # o or m
    is_limit = False
    if limit_tok[0].value == "m":
        is_limit = True

    out_toks = expander.parse_immediate_token(expand=True, skip_whitespace=True)
    if not out_toks:
        return None

    # convert to \mathop{\mathrm{...}}
    math_rm_toks = [
        Token(TokenType.CONTROL_SEQUENCE, "mathrm"),
        *wrap_tokens_in_braces(out_toks),
    ]

    limit_token = Token(
        TokenType.CONTROL_SEQUENCE, "limits" if is_limit else "nolimits"
    )

    return [
        Token(TokenType.CONTROL_SEQUENCE, "mathop"),
        *wrap_tokens_in_braces(math_rm_toks),
        limit_token,
    ]


def newmcodes_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    # supposed to reset math catcodes..
    return []


def make_convert_to_str_handler(text: str) -> Handler:
    tokens = convert_str_to_default_token_catcodes(text)

    def convert_to_str_handler(
        expander: ExpanderCore, token: Token
    ) -> Optional[List[Token]]:
        return tokens.copy()

    return convert_to_str_handler


def frac_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    # put in braces to be certain
    toks1 = expander.parse_immediate_token(skip_whitespace=True, expand=True)
    toks2 = expander.parse_immediate_token(skip_whitespace=True, expand=True)
    if toks1 is None or toks2 is None:
        expander.logger.warning("frac: Missing argument")
        return None
    return [token, *wrap_tokens_in_braces(toks1), *wrap_tokens_in_braces(toks2)]


def register_number_format_handlers(expander: ExpanderCore):
    expander.register_handler("number", number_handler, is_global=True)
    expander.register_handler("num", num_handler, is_global=True)
    expander.register_handler("romannumeral", romannumeral_handler, is_global=True)
    expander.register_handler("mathchoice", mathchoice_handler, is_global=True)
    expander.register_handler("qopname", qopname_handler, is_global=True)
    expander.register_handler("newmcodes@", newmcodes_handler, is_global=True)

    # frac
    expander.register_handler("frac", frac_handler, is_global=True)

    primitive_num_cmds = {
        "@ne": 1,
        "m@ne": -1,
        "z@": 0,
        "tw@": 2,
        "thr@@": 3,
        "sixt@@n": 16,
        "@xxxii": 32,
        "@cclv": 255,
        "@cclvi": 256,
        "@m": 1000,
        "@M": 10000,
        "@Mi": 10001,
        "@Mii": 10002,
        "@Miii": 10003,
        "@Miv": 10004,
        "@MM": 20000,
        "@vpt": 5,
        "@vipt": 6,
        "@viipt": 7,
        "@viiipt": 8,
        "@ixpt": 9,
        "@xpt": 10,
        "@xipt": 10.95,
        "@xiipt": 12,
        "@xivpt": 14.4,
        "@xviipt": 17.28,
        "@xxpt": 20.74,
        "@xxvpt": 24.88,
        "col@number": 1,  # default to 1
        "active": 13,
        "letter": 11,
        "other": 12,
        "endlinechar": 5,
    }
    for cmd, v in primitive_num_cmds.items():
        expander.register_handler(
            cmd,
            make_convert_to_str_handler(str(v)),
            is_global=True,
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_number_format_handlers(expander)

    text = r"\num{1.234567890}"
    out = expander.expand(text)
    print(out)
