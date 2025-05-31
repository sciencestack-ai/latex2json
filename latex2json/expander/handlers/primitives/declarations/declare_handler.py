from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.primitives.declarations.newcommand import (
    NewCommandMacro,
    get_newcommand_name,
)
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token, TokenType
from typing import Optional

ignored_declare_pattern_N_blocks = {
    # Font declarations
    "DeclareFontFamily": 3,
    "DeclareFontShape": 6,
    "DeclareMathAlphabet": 5,
    "SetMathAlphabet": 6,
    "DeclareSymbolFontAlphabet": 2,
    "DeclareMathVersion": 1,
    "DeclareMathSymbol": 4,
    # Package/class options
    "DeclareOption": 2,
    "DeclareOptionX": 2,
}


def declare_math_operator_handler(
    expander: ExpanderCore, token: Token
) -> Optional[list[Token]]:
    r"""Handler for \DeclareMathOperator"""
    has_star = expander.parse_asterisk()
    expander.skip_whitespace()

    # Parse the operator name
    name = get_newcommand_name(expander)
    if name is None:
        return None

    # Parse the operator text
    expander.skip_whitespace()
    definition = expander.parse_brace_as_tokens()
    if definition is None:
        expander.logger.warning(
            f"Warning: \\DeclareMathOperator requires an operator definition"
        )
        return None

    # Wrap the definition in \mathop{\mathrm{...}}
    wrapped_definition = [
        Token(TokenType.CONTROL_SEQUENCE, "mathop"),
        BEGIN_BRACE_TOKEN.copy(),
        Token(TokenType.CONTROL_SEQUENCE, "mathrm"),
        BEGIN_BRACE_TOKEN.copy(),
        *definition,
        END_BRACE_TOKEN.copy(),
        END_BRACE_TOKEN.copy(),
        Token(TokenType.CONTROL_SEQUENCE, "limits" if has_star else "nolimits"),
    ]

    def operator_handler(expander: ExpanderCore, token: Token) -> Optional[list[Token]]:
        expander.push_tokens(wrapped_definition)
        return []

    expander.register_macro(
        name,
        Macro(name, operator_handler, definition=wrapped_definition),
        is_global=True,
    )
    return []


def declare_paired_delimiter_handler(
    expander: ExpanderCore, token: Token
) -> Optional[list[Token]]:
    r"""Handler for \DeclarePairedDelimiter"""
    name = get_newcommand_name(expander)
    if name is None:
        return None

    blocks = expander.parse_braced_blocks(2)
    if len(blocks) != 2:
        expander.logger.warning(
            f"Warning: \\DeclarePairedDelimiter requires two delimiter pairs"
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
        name,
        Macro(name, paired_delim_handler),
        is_global=True,
    )

    return []


def make_declare_ignore_handler(pattern: str, n_blocks: int):
    def ignore_handler(expander: ExpanderCore, token: Token) -> Optional[list[Token]]:
        blocks = expander.parse_braced_blocks(n_blocks)
        return []

    return ignore_handler


def register_declare_commands(expander: ExpanderCore):
    expander.register_macro(
        "\\DeclareRobustCommand",
        NewCommandMacro("\\DeclareRobustCommand", allow_redefine=True),
        is_global=True,
    )
    expander.register_handler(
        "\\DeclareMathOperator",
        declare_math_operator_handler,
        is_global=True,
    )

    expander.register_handler(
        "\\DeclarePairedDelimiter",
        declare_paired_delimiter_handler,
        is_global=True,
    )

    for command, n_blocks in ignored_declare_pattern_N_blocks.items():
        expander.register_handler(
            command,
            make_declare_ignore_handler(command, n_blocks),
            is_global=True,
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_declare_commands(expander)

    # Test DeclareRobustCommand
    expander.expand(r"\DeclareRobustCommand* {\rchi}{{\mathpalette\irchi\relax}}")
    out1 = expander.expand(r"\rchi")
    # print("DeclareRobustCommand test:", out)

    # Test DeclareMathOperator
    expander.expand(r"\DeclareMathOperator*{\sech}{sech}")
    out2 = expander.expand(r"\sech")
    # print("DeclareMathOperator test:", out)

    # out3 = expander.expand(r"\DeclareMathAlphabet {\mathbf}{OT1}{cmr}{b}{n} POST")

    expander.expand(r"\DeclarePairedDelimiter\brc{[}{]}")
    out4 = expander.expand(r"$1+1=\brc{2343}3$")
