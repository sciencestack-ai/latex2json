from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import wrap_tokens_in_braces


def jobname_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \jobname  ->  returns the job name (usually filename without extension)
    Since we don't track the job name, return a placeholder.
    """
    # Return a generic job name
    return expander.convert_str_to_tokens("document")


def csgdef_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \csgdef{name}{body}  ->  \expandafter\gdef\csname name\endcsname{body}
    Global define of a control sequence constructed from a name.
    """
    expander.skip_whitespace()
    name_tokens = expander.parse_brace_as_tokens() or []
    cmd_name = "".join(t.value for t in name_tokens).strip()

    expander.skip_whitespace()
    body_tokens = expander.parse_brace_as_tokens() or []

    if cmd_name:
        cmd = Token(TokenType.CONTROL_SEQUENCE, cmd_name)
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "gdef"),
                cmd,
            ]
            + wrap_tokens_in_braces(body_tokens)
        )
    return []


def csdef_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \csdef{name}{body}  ->  \expandafter\def\csname name\endcsname{body}
    Define a control sequence constructed from a name.
    """
    expander.skip_whitespace()
    name_tokens = expander.parse_brace_as_tokens() or []
    cmd_name = "".join(t.value for t in name_tokens).strip()

    expander.skip_whitespace()
    body_tokens = expander.parse_brace_as_tokens() or []

    if cmd_name:
        cmd = Token(TokenType.CONTROL_SEQUENCE, cmd_name)
        expander.push_tokens(
            [
                Token(TokenType.CONTROL_SEQUENCE, "def"),
                cmd,
            ]
            + wrap_tokens_in_braces(body_tokens)
        )
    return []


def csuse_handler(expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
    r"""
    \csuse{name}  ->  \csname name\endcsname
    Use a control sequence constructed from a name.
    """
    expander.skip_whitespace()
    name_tokens = expander.parse_brace_as_tokens() or []
    cmd_name = "".join(t.value for t in name_tokens).strip()

    if cmd_name:
        cmd = Token(TokenType.CONTROL_SEQUENCE, cmd_name)
        expander.push_tokens([cmd])
    return []


def register_other_primitives(expander: ExpanderCore):
    """
    Register LaTeX primitive macros defined via ltx_text.
    Consolidates simple macro definitions that don't require Python handlers.
    """
    # Register jobname primitive
    expander.register_handler("\\jobname", jobname_handler, is_global=True)

    # Register etoolbox-style cs* commands
    expander.register_handler("\\csgdef", csgdef_handler, is_global=True)
    expander.register_handler("\\csdef", csdef_handler, is_global=True)
    expander.register_handler("\\csuse", csuse_handler, is_global=True)

    # @firstofone, @firstoftwo, @secondoftwo
    ltx_text_at_x_of_x = r"""
\long\def\@firstofone#1{#1}
\long\def\@firstoftwo#1#2{#1}
\long\def\@secondoftwo#1#2{#2}
"""
    expander.expand_ltx(ltx_text_at_x_of_x)

    # @dblarg, @xdblarg
    ltx_text_dblarg = r"""
\long\def\@dblarg#1{\@ifnextchar[{#1}{\@xdblarg{#1}}}
\long\def\@xdblarg#1#2{#1[{#2}]{#2}}
"""
    expander.expand_ltx(ltx_text_dblarg)

    # @addpunct
    #     ltx_addpunct = r"""
    # \def\@addpunct#1{%
    #   \futurelet\@let@token\@addpunct@i #1%
    # }

    # \def\@addpunct@i#1{%
    #   \ifx\@let@token.%
    #     \if.#1\else#1\fi
    #   \else
    #     #1%
    #   \fi
    # }
    # """
    ltx_addpunct = r"""
    \def\@addpunct#1{#1} % just keep it simple??..
"""
    expander.expand_ltx(ltx_addpunct)
