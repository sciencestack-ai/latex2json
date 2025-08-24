from dataclasses import dataclass
from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token, TokenType


def let_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    cmd_name = expander.parse_command_name()
    if not cmd_name:
        expander.logger.warning(
            f"Warning: \\let expects a command node, but found {cmd_name}"
        )
        return None

    expander.skip_whitespace()
    expander.parse_equals()

    def_tok = expander.consume()

    if not def_tok:
        expander.logger.warning(
            f"Warning: \\let expects a definition, but found {def_tok}"
        )
        return None

    is_control_sequence = def_tok.type == TokenType.CONTROL_SEQUENCE
    if is_control_sequence:
        # check if existing macro
        macro = expander.get_macro(def_tok.value)
        if macro:
            macro_copy = macro.copy()

            def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
                out = macro.handler(expander, token)
                if out:
                    expander.push_tokens(out)
                return []

            macro_copy.handler = handler
            expander.register_macro(
                cmd_name, macro_copy, is_global=False, is_user_defined=True
            )
            return []

    def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        if is_control_sequence:
            # if the definition is a control sequence that is not found, we return it as is
            return [def_tok.copy()]

        expander.push_tokens([def_tok.copy()])
        return []

    macro = Macro(cmd_name, handler, [def_tok], type=MacroType.CHAR)
    expander.register_macro(cmd_name, macro, is_global=False, is_user_defined=True)

    return []


def futurelet_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    temp_cmd = expander.peek()
    if not temp_cmd or temp_cmd.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(
            f"Warning: \\futurelet expects <control1><control2>, but <control1> is {temp_cmd}"
        )
        return None

    expander.consume()
    temp_name = temp_cmd.value  # e.g., '\next'

    expander.skip_whitespace()
    handler_cmd = expander.consume()
    if not handler_cmd or handler_cmd.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(
            f"Warning: \\futurelet expects <control1><control2>, but <control2> is {handler_cmd}"
        )
        return None

    handler_macro = expander.get_macro(handler_cmd.value)
    if not handler_macro or not handler_macro.handler:
        expander.logger.warning(
            f"\\futurelet: handler macro {handler_cmd.value} not defined"
        )
        return None

    expander.skip_whitespace()

    # 1. Peek at the next token in the stream, but do NOT consume it
    next_token = expander.peek()
    if not next_token:
        expander.logger.warning("Warning: \\futurelet: no token to peek at.")
        return None

    # 2. Define temp macro as raw passthrough (like \let), without expanding
    def temp_macro_handler(exp: ExpanderCore, t: Token) -> Optional[List[Token]]:
        return [next_token]

    expander.register_macro(
        temp_name,
        Macro(temp_name, temp_macro_handler, [next_token], type=MacroType.CHAR),
        is_global=False,
        is_user_defined=True,
    )

    # Push the handler macro back into the input stream to be expanded now
    expander.push_tokens([handler_cmd])

    return []


def register_let(expander: ExpanderCore):
    expander.register_handler(
        "\\let",
        let_handler,
        is_global=True,
    )
    expander.register_handler(
        "\\futurelet",
        futurelet_handler,
        is_global=True,
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander
    from latex2json.tokens.utils import strip_whitespace_tokens

    expander = Expander()
    register_let(expander)
    # expander.expand(r"\let\foo=3")
    # expander.expand(r"\foo")

    text = r"""
    \def\lookahead{
        \futurelet\next\checkcolon
    }

    \def\checkcolon{%
        \ifx\next:
            COLON
        \else
            NOT COLON
        \fi
    }
    \lookahead :
""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    # print(out)
