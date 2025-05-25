from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import CATCODE_MEANINGS, Catcode
from latex2json.tokens.types import Token, TokenType

from latex2json.expander.handlers.primitives.catcode import CatcodeHandler


def the_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    tok = expander.peek()
    if not tok:
        return None

    if tok.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(
            f"Warning: \\the expects a control sequence, but found {tok}"
        )
        return None

    name = tok.value

    if name == "catcode":
        expander.consume()
        return CatcodeHandler.getter(expander, token)
    else:
        # try to parse as a register
        parsed = expander.parse_register()
        if parsed:
            return expander.get_register_value_as_tokens(parsed[0], parsed[1])

    return []


def show_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    tok = expander.consume()
    if not tok:
        return None

    if tok.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(
            f"Warning: \\show expects a control sequence, but found {tok}"
        )
        return None

    name = tok.value
    macro = expander.get_macro(name)
    if macro:
        definition = expander.convert_tokens_to_str(macro.definition)
        expander.logger.debug(f"\\show: {name} -> {definition}")
        return []
    else:
        expander.logger.debug(f"\\show: {name} is undefined")
        return []

    return None


def typeout_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    tok = expander.peek()
    if not tok:
        return None

    tok = expander.parse_immediate_token()
    if not tok:
        return None

    exp = expander.expand_tokens(tok)
    exp_str = expander.convert_tokens_to_str(exp)
    expander.logger.debug(f"\\typeout: {exp_str}")
    return []


def meaning_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    tok = expander.peek()
    if not tok:
        return None

    tok = expander.consume()
    if not tok:
        return None

    out_tokens: List[Token] = [tok]
    if tok.type == TokenType.CONTROL_SEQUENCE:
        macro = expander.get_macro(tok.value)
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

    return [tok]


def register_debug_handlers(expander: ExpanderCore):
    expander.register_handler("\\the", the_handler, is_global=True)
    expander.register_handler("\\show", show_handler, is_global=True)
    expander.register_handler("\\typeout", typeout_handler, is_global=True)
    expander.register_handler("\\meaning", meaning_handler, is_global=True)
    expander.register_handler("\\string", string_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander
    import logging

    # Configure logging properly
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    logger = logging.getLogger("expander")

    expander = Expander(logger=logger)

    text = r"""

\makeatletter

% 1. Generic lookahead function
\def\lookahead{\futurelet\next\@check}

% 2. Dispatch logic
\def\@check{%
  \ifx\next\bgroup
    \typeout{[lookahead] Next token is a group!}%
  \else
    \ifx\next\somecmd
      \typeout{[lookahead] Next token is \string\somecmd!}%
    \else
      \typeout{[lookahead] Next token is something else.}%
    \fi
  \fi
}

% 3. Dummy macro for testing
\def\somecmd{This is a macro.}

% ----- Test runs -----
% A: Peek a brace
\lookahead{123}

% B: Peek a macro
\lookahead\somecmd

% C: Peek a character
\lookahead!

\makeatother
""".strip()
    out = expander.expand(text)
    # print(out)
