from dataclasses import dataclass
from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token, TokenType


def let_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    cmd = expander.peek()
    if not cmd or not expander.is_control_sequence(cmd):
        expander.logger.warning(
            f"Warning: \\let expects a command node, but found {cmd}"
        )
        return None

    expander.consume()

    expander.skip_whitespace()
    expander.parse_equals()

    def_tok = expander.consume()

    if not def_tok:
        expander.logger.warning(
            f"Warning: \\let expects a definition, but found {def_tok}"
        )
        return None

    is_control_sequence = expander.is_control_sequence(def_tok)
    if expander.is_control_sequence(def_tok):
        # check if existing macro
        macro = expander.get_macro(def_tok)
        if macro:
            macro_copy = macro.copy()

            def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
                out = macro.handler(expander, token)
                if out:
                    expander.push_tokens(out)
                return []

            macro_copy.handler = handler
            expander.register_macro(
                cmd, macro_copy, is_global=False, is_user_defined=True
            )
            return []

    def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        if is_control_sequence:
            # if the definition is a control sequence that is not found, we return it as is
            return [def_tok.copy()]

        expander.push_tokens([def_tok.copy()])
        return []

    macro = Macro(cmd, handler, [def_tok], type=MacroType.CHAR)
    expander.register_macro(cmd, macro, is_global=False, is_user_defined=True)

    return []


def futurelet_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    temp_cmd = expander.peek()
    if not temp_cmd or not expander.is_control_sequence(temp_cmd):
        expander.logger.warning(
            f"Warning: \\futurelet expects <control1><control2>, but <control1> is {temp_cmd}"
        )
        return None

    expander.consume()

    expander.skip_whitespace()
    handler_cmd = expander.consume()
    if not handler_cmd or not expander.is_control_sequence(handler_cmd):
        expander.logger.warning(
            f"Warning: \\futurelet expects <control1><control2>, but <control2> is {handler_cmd}"
        )
        return None

    handler_macro = expander.get_macro(handler_cmd)
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
        temp_cmd,
        Macro(temp_cmd.value, temp_macro_handler, [next_token], type=MacroType.CHAR),
        is_global=False,
        is_user_defined=True,
    )

    # Push the handler macro back into the input stream to be expanded now
    expander.push_tokens([handler_cmd])

    return []


def letltxmacro_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    cmd = expander.parse_command_name_token()
    expander.skip_whitespace()
    target_cmd = expander.parse_command_name_token()
    if not cmd:
        expander.logger.warning("\\letltxmacro: Requires a name argument")
        return None
    if not target_cmd:
        expander.logger.warning("\\letltxmacro: Requires a target name argument")
        return None

    target_macro = expander.get_macro(target_cmd)
    if target_macro is None:
        # push the control sequence as is
        def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
            return [target_cmd]

        expander.register_handler(cmd, handler, is_global=False, is_user_defined=True)

    else:
        macro = target_macro.copy()
        macro.name = cmd.value
        expander.register_macro(cmd, macro, is_global=False, is_user_defined=True)

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

    expander.register_macro(
        "\\LetLtxMacro",
        Macro("\\LetLtxMacro", letltxmacro_handler),
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
