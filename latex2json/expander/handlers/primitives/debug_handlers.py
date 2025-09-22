from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.catcodes import CATCODE_MEANINGS, Catcode
from latex2json.tokens.types import Token, TokenType

from latex2json.expander.handlers.primitives.catcode_sfcode_handlers import (
    CatcodeHandler,
    SFCodeHandler,
)


def the_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    tok = expander.peek()
    if not tok:
        return None

    if not expander.is_control_sequence(tok):
        expander.logger.warning(f"\\the expects a control sequence, but found {tok}")
        return None

    name = tok.value

    if name == "catcode":
        expander.consume()
        return CatcodeHandler.getter(expander, token)
    elif name == "sfcode":
        expander.consume()
        return SFCodeHandler.getter(expander, token)
    else:
        # try to parse as a register
        parsed = expander.parse_register()
        if parsed:
            return expander.get_register_value_as_tokens(parsed[0], parsed[1])

        # # just use the macro handler itself...?
        # macro = expander.get_macro(name)
        # if macro:
        #     return macro.handler(expander, token)

    return []


def show_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    tok = expander.consume()
    if not tok:
        return None

    macro = expander.get_macro(tok)
    if not macro:
        expander.logger.debug(f"\\show: {tok.value} is undefined")
        return []
    definition = expander.convert_tokens_to_str(macro.definition)
    expander.logger.debug(f"\\show: {tok.value} -> {definition}")
    return []


def make_print_handler(name: str):
    def print_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        tok = expander.peek()
        if not tok:
            return None

        tokens = expander.parse_immediate_token(expand=True)
        if not tokens:
            return None

        exp_str = expander.convert_tokens_to_str(tokens)
        expander.logger.debug(f"\\{name}: {exp_str}")
        return []

    return print_handler


def meaning_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    tok = expander.peek()
    if not tok:
        return None

    tok = expander.consume()
    if not tok:
        return None

    out_tokens: List[Token] = [tok]
    if expander.is_control_sequence(tok):
        macro = expander.get_macro(tok)
        if not macro:
            out_tokens = expander.convert_str_to_tokens("undefined")
        else:
            out_tokens = expander.convert_str_to_tokens("macro:->") + macro.definition
    else:
        # in tex there is a mapping of immediate tokens to their meaning
        # e.g. '{' -> begin-group character, catcode 12 is the character, etc
        meaning_str = CATCODE_MEANINGS[tok.catcode]
        meaning_str += " " + tok.value
        out_tokens = expander.convert_str_to_tokens(meaning_str)

    # expander.logger.debug(f"\\meaning: {out_tokens}")
    return out_tokens


def string_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    tok = expander.peek()
    if not tok:
        return None

    tok = expander.consume()
    if not tok:
        return None

    if tok.type == TokenType.CONTROL_SEQUENCE:
        # convert all to character tokens
        tok_str = "\\" + tok.value
        out_tokens = expander.convert_str_to_tokens(tok_str, catcode=Catcode.LETTER)
        return out_tokens

    return [tok]


def escapechar_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    # ignore it..
    if expander.parse_equals():
        expander.skip_whitespace()
    expander.parse_integer()
    return []


def latexerror_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    tokens = expander.parse_immediate_token(expand=True, skip_whitespace=True)
    code = expander.parse_immediate_token(expand=True, skip_whitespace=True)
    if not tokens:
        return []
    token_str = expander.convert_tokens_to_str(tokens)
    expander.logger.info(f"\\@latex@error: {token_str}")
    return []


def register_debug_handlers(expander: ExpanderCore):
    expander.register_handler("\\the", the_handler, is_global=True)
    expander.register_handler("\\show", show_handler, is_global=True)
    expander.register_handler(
        "\\typeout", make_print_handler("typeout"), is_global=True
    )
    expander.register_handler(
        "\\message", make_print_handler("message"), is_global=True
    )
    expander.register_handler("\\meaning", meaning_handler, is_global=True)
    expander.register_handler("\\string", string_handler, is_global=True)
    expander.register_handler("\\escapechar", escapechar_handler, is_global=True)
    expander.register_handler("\\@latex@error", latexerror_handler, is_global=True)

    debug_ignore_patterns = {
        "ClassWarningNoLine": "{{",
        "ClassWarning": "{{",
        "ClassInfo": "{{",
        "ClassError": "{{{",
        "ClassNotice": "{{",
        "ClassDebug": "{{",
        "PackageError": "{{{",
        "PackageWarning": "{{",
    }

    register_ignore_handlers_util(
        expander,
        debug_ignore_patterns,
        expand=False,
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander
    import logging

    # Configure logging properly
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    logger = logging.getLogger("expander")

    expander = Expander(logger=logger)

    text = r"""
\makeatletter
\def\test{test}
\@latex@error{\noexpand\test}{@ehc}
""".strip()
    out = expander.expand(text)
    print(out)
