from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.expander.handlers.primitives.declarations.newcommand import (
    NewCommandMacro,
)
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token, TokenType
from typing import Callable, Optional

from latex2json.tokens.utils import wrap_tokens_in_braces

ignored_declare_patterns = {
    # Font declarations
    "DeclareFontFamily": 3,
    "DeclareFontShape": 6,
    "SetMathAlphabet": 6,
    "DeclareSymbolFont": 5,
    "DeclareSymbolFontAlphabet": 2,
    "DeclareFontSubstitution": 4,
    # Package/class options
    # "DeclareOption": "*{", # need custom handler for *{ vs {{
    "DeclareGraphicsExtensions": 1,
    # MATH
    "DeclareMathAlphabet": 5,
    "DeclareMathVersion": 1,
    # math symbol declarations http://labmaster.mi.infn.it/wwwasdoc.web.cern.ch/wwwasdoc/TL8/texmf/doc/latex/base/html/fntguide/node18.html
    # DeclareMathSymbol and DeclareMathDelimiter handled separately to register the command
    "DeclareMathAccent": 4,
    "DeclareMathRadical": 5,
    "DeclareGraphicsRule": 4,
}


def _make_declare_math_cmd_handler(n_remaining_args: int):
    r"""Create a handler for \DeclareMathSymbol or \DeclareMathDelimiter.

    These register the first argument (a command name) as a passthrough math symbol,
    then consume the remaining font-related arguments. This ensures the command is
    known to \let and other copiers, and passes through to the output for KaTeX.
    """

    def handler(expander: ExpanderCore, token: Token) -> Optional[list[Token]]:
        expander.skip_whitespace()
        cmd = expander.parse_command_name_token()
        if cmd is None:
            expander.logger.warning(f"{token.value} expects a command name")
            return None

        # Consume remaining font-related arguments
        expander.parse_braced_blocks(n_remaining_args, check_immediate_tokens=True)

        # Register the command as a passthrough (token passes through to output)
        def passthrough_handler(
            expander: ExpanderCore, token: Token
        ) -> Optional[list[Token]]:
            return [token]

        expander.register_macro(
            cmd,
            Macro(cmd, passthrough_handler, type=MacroType.CHAR),
            is_global=True,
            is_user_defined=True,
        )
        return []

    return handler


def declare_math_operator_handler(
    expander: ExpanderCore, token: Token
) -> Optional[list[Token]]:
    r"""Handler for \DeclareMathOperator"""
    has_star = expander.parse_asterisk()
    expander.skip_whitespace()

    # Parse the operator name
    cmd = expander.parse_command_name_token()
    if cmd is None:
        expander.logger.warning(
            f"\\DeclareMathOperator expects a command name, but found {expander.peek()}"
        )
        return None

    # Parse the operator text
    expander.skip_whitespace()
    definition = expander.parse_brace_as_tokens()
    if definition is None:
        expander.logger.warning(
            f"\\DeclareMathOperator requires an operator definition"
        )
        return None

    # Wrap the definition in \mathop{\mathrm{...}}
    wrapped_definition = [
        Token(TokenType.CONTROL_SEQUENCE, "mathop"),
        BEGIN_BRACE_TOKEN.copy(),
        Token(TokenType.CONTROL_SEQUENCE, "mathrm"),
        *wrap_tokens_in_braces(definition),
        END_BRACE_TOKEN.copy(),
        Token(TokenType.CONTROL_SEQUENCE, "limits" if has_star else "nolimits"),
    ]

    def operator_handler(expander: ExpanderCore, token: Token) -> Optional[list[Token]]:
        expander.push_tokens(wrapped_definition)
        return []

    expander.register_macro(
        cmd,
        Macro(cmd, operator_handler, definition=wrapped_definition),
        is_global=True,
        is_user_defined=True,
    )
    return []


def declare_paired_delimiter_handler(
    expander: ExpanderCore, token: Token
) -> Optional[list[Token]]:
    r"""Handler for \DeclarePairedDelimiter"""
    cmd = expander.parse_command_name_token()
    if cmd is None:
        expander.logger.warning(
            f"\\DeclarePairedDelimiter expects a command name, but found {expander.peek()}"
        )
        return None

    blocks = expander.parse_braced_blocks(2)
    if len(blocks) != 2:
        expander.logger.warning(
            f"\\DeclarePairedDelimiter requires two delimiter pairs"
        )
        return None

    delim1 = blocks[0]
    delim2 = blocks[1]

    def paired_delim_handler(
        expander: ExpanderCore, token: Token
    ) -> Optional[list[Token]]:
        expander.skip_whitespace()
        tokens = expander.parse_immediate_token()
        expander.push_tokens(delim1 + tokens + delim2)
        return []

    expander.register_macro(
        cmd,
        Macro(cmd, paired_delim_handler),
        is_global=True,
        is_user_defined=True,
    )

    return []


def declare_option_handler(
    expander: ExpanderCore, token: Token
) -> Optional[list[Token]]:
    r"""Handler for \DeclareOption: Ignore"""
    expander.skip_whitespace()
    has_star = expander.parse_asterisk()
    expander.skip_whitespace()
    braced_blocks = 1 if has_star else 2
    blocks = expander.parse_braced_blocks(braced_blocks, check_immediate_tokens=True)
    # if len(blocks) != braced_blocks:
    #     expander.logger.warning(
    #         f"\\DeclareOption requires {braced_blocks} braced blocks"
    #     )
    #     return None
    return []


def delcare_textfont_handler(
    expander: ExpanderCore, token: Token
) -> Optional[list[Token]]:
    r"""Handler for \DeclareTextFontCommand
    \DeclareTextFontCommand{\myfont}{\textbf}
    """
    expander.skip_whitespace()
    cmd_tok = expander.parse_command_name_token()
    expander.skip_whitespace()
    definition = expander.parse_brace_as_tokens(expand=False)
    if not cmd_tok:
        expander.logger.warning("\\DeclareTextFontCommand expects {cmd}{definition}")
        return None

    def handler(expander: ExpanderCore, token: Token) -> Optional[list[Token]]:
        expander.push_tokens(definition)
        return []

    expander.register_handler(cmd_tok, handler, is_global=True, is_user_defined=True)

    return []


def declare_fixedfont_handler(
    expander: ExpanderCore, token: Token
) -> Optional[list[Token]]:
    r"""Handler for \DeclareFixedFont
    \DeclareFixedFont\trfont{OT1}{phv}{b}{sc}{11}
    """
    expander.skip_whitespace()
    cmd_tok = expander.parse_command_name_token()
    expander.skip_whitespace()
    expander.parse_braced_blocks(5)

    # just ignore?
    def handler(expander: ExpanderCore, token: Token) -> Optional[list[Token]]:
        return []

    expander.register_handler(cmd_tok, handler, is_global=True, is_user_defined=True)

    return []


def register_declare_commands(expander: ExpanderCore):
    expander.register_macro(
        "\\DeclareRobustCommand",
        NewCommandMacro("\\DeclareRobustCommand", allow_redefine=True),
        is_global=True,
    )
    expander.register_macro(
        "\\DeclareMathOperator",
        Macro(
            "\\DeclareMathOperator",
            declare_math_operator_handler,
            type=MacroType.DECLARATION,
        ),
        is_global=True,
    )

    # DeclareMathSymbol: \DeclareMathSymbol{\cmd}{\type}{font}{slot} (3 remaining args)
    expander.register_macro(
        "\\DeclareMathSymbol",
        Macro(
            "\\DeclareMathSymbol",
            _make_declare_math_cmd_handler(3),
            type=MacroType.DECLARATION,
        ),
        is_global=True,
    )
    # DeclareMathDelimiter: \DeclareMathDelimiter{\cmd}{\type}{font}{slot}{lgfont}{lgslot} (5 remaining args)
    expander.register_macro(
        "\\DeclareMathDelimiter",
        Macro(
            "\\DeclareMathDelimiter",
            _make_declare_math_cmd_handler(5),
            type=MacroType.DECLARATION,
        ),
        is_global=True,
    )

    expander.register_macro(
        "\\DeclarePairedDelimiter",
        Macro(
            "\\DeclarePairedDelimiter",
            declare_paired_delimiter_handler,
            type=MacroType.DECLARATION,
        ),
        is_global=True,
    )

    for cmd in ["DeclareOption", "DeclareOptionX"]:
        expander.register_macro(
            f"\\{cmd}",
            Macro(
                f"\\{cmd}",
                declare_option_handler,
                type=MacroType.DECLARATION,
            ),
            is_global=True,
        )

    expander.register_macro(
        "\\DeclareTextFontCommand",
        Macro(
            "\\DeclareTextFontCommand",
            delcare_textfont_handler,
            type=MacroType.DECLARATION,
        ),
        is_global=True,
    )
    expander.register_macro(
        "\\DeclareFixedFont",
        Macro(
            "\\DeclareFixedFont",
            declare_fixedfont_handler,
            type=MacroType.DECLARATION,
        ),
        is_global=True,
    )

    register_ignore_handlers_util(expander, ignored_declare_patterns)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_declare_commands(expander)

    # # Test DeclareRobustCommand
    # expander.expand(r"\DeclareRobustCommand* {\rchi}{{\mathpalette\irchi\relax}}")
    # out1 = expander.expand(r"\rchi")
    # # print("DeclareRobustCommand test:", out)

    # # Test DeclareMathOperator
    # expander.expand(r"\DeclareMathOperator*{\sech}{sech}")
    # out2 = expander.expand(r"\sech")
    # # print("DeclareMathOperator test:", out)

    # # out3 = expander.expand(r"\DeclareMathAlphabet {\mathbf}{OT1}{cmr}{b}{n} POST")

    # expander.expand(r"\DeclarePairedDelimiter\brc{[}{]}")
    # out4 = expander.expand(r"$1+1=\brc{2343}3$")

    text = r"""
    \DeclareTextFontCommand{\myfont}{\textbf}
    \myfont{Hello}
    """
    out = expander.expand(text)
    print(out)
