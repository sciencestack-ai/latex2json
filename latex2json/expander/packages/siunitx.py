from typing import List
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import convert_str_to_tokens
from latex2json.latex_maps.si_unit_map import SI_UNIT_MAP


def _convert_unit_tokens(tokens: List[Token]) -> List[Token]:
    out_tokens: List[Token] = []
    for t in tokens:
        if t.type == TokenType.CONTROL_SEQUENCE:
            v = t.value
            if v in SI_UNIT_MAP:
                converted_v = SI_UNIT_MAP[v]
                out_tokens.extend(
                    convert_str_to_tokens(converted_v, catcode=Catcode.LETTER)
                )
                continue
        out_tokens.append(t)
    return out_tokens


def si_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    unit_tokens = expander.parse_immediate_token()
    if unit_tokens is None:
        return []

    unit_tokens = _convert_unit_tokens(unit_tokens)
    expander.push_tokens(unit_tokens)
    return []


def SI_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    number_tokens = expander.parse_immediate_token() or []
    expander.skip_whitespace()
    unit_tokens = expander.parse_immediate_token() or []
    unit_tokens = _convert_unit_tokens(unit_tokens)
    expander.push_tokens(number_tokens + unit_tokens)
    return []


def register_siunitx(expander: ExpanderCore):
    expander.register_handler("si", si_handler, is_global=True)
    expander.register_handler("SI", SI_handler, is_global=True)

    ignore_patterns = {
        "sisetup": 1,
    }

    register_ignore_handlers_util(expander, ignore_patterns)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    text = r"""
    1x \si{\metre\%}
    \SI{100}{\kilogram}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
