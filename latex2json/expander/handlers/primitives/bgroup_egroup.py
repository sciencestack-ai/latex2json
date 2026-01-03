from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token, TokenType
from latex2json.tokens.utils import is_end_group_token, wrap_tokens_in_braces


def bgroup_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.push_tokens([BEGIN_BRACE_TOKEN.copy()])
    return []


def egroup_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.push_tokens([END_BRACE_TOKEN.copy()])
    return []


def is_end_group_tokens(tok: Token) -> bool:
    return is_end_group_token(tok) or (
        tok.type == TokenType.CONTROL_SEQUENCE
        and tok.value in ["end", "egroup", "endgroup"]
    )


def aftergroup_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    after_toks = expander.parse_immediate_token(skip_whitespace=True)
    if after_toks is None:
        return None
    tokens = expander.parse_tokens_until(is_end_group_tokens, consume_predicate=False)
    tokens += after_toks
    expander.push_tokens(tokens)
    return []


# NOTE: The alternative implementation below attempted to parse and reinject the end group
# token (e.g., \end{...}) after collecting tokens until the group boundary. However, this
# approach led to parsing complications because the reinjected end token would be processed
# out of its original context, causing issues with environment matching and scope resolution.
# We settled for the simpler approach above which does not consume/reinject the end group
# sequence, leaving it in place to be processed naturally by the parser.
# def aftergroup_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
#     after_toks = expander.parse_immediate_token(skip_whitespace=True)
#     if after_toks is None:
#         return None
#     tokens = expander.parse_tokens_until(is_end_group_tokens, consume_predicate=False)

#     # parse the end token itself
#     end_group_tok = expander.consume()
#     if end_group_tok:
#         tokens += [end_group_tok]
#         if end_group_tok.value == "end":
#             # parse the brace together
#             brace_toks = expander.parse_immediate_token(
#                 skip_whitespace=True, expand=False
#             )
#             if brace_toks:
#                 tokens += wrap_tokens_in_braces(brace_toks)
#     tokens += after_toks
#     expander.push_tokens(tokens)


# useful to define Macro as type=MacroType.CHAR so that it can be used in \ifx etc
def register_bgroup(expander: ExpanderCore):
    for bgroup in ["bgroup", "begingroup"]:
        expander.register_macro(
            bgroup,
            Macro(
                bgroup,
                bgroup_handler,
                definition=[BEGIN_BRACE_TOKEN.copy()],
                type=MacroType.CHAR,
            ),
            is_global=True,
        )
    for egroup in ["egroup", "endgroup"]:
        expander.register_macro(
            egroup,
            Macro(
                egroup,
                egroup_handler,
                definition=[END_BRACE_TOKEN.copy()],
                type=MacroType.CHAR,
            ),
            is_global=True,
        )

    # expander.register_handler("begingroup", begingroup_handler, is_global=True)
    # expander.register_handler("endgroup", endgroup_handler, is_global=True)

    expander.register_handler("aftergroup", aftergroup_handler, is_global=True)


if __name__ == "__main__":

    from latex2json.expander.expander import Expander

    expander = Expander()

    text = r"""
\newcommand\lft{\mathopen{}\left}
\newcommand\rgt{\aftergroup\mathclose\aftergroup{\aftergroup}\right}

\begin{gather}
  \mathbf{\Delta C}_k = 
  \lft( 1 - \frac{\alpha_k}{d_k} \rgt) \mathbf{c}_k^\mathrm{in} + 
  \lft( \frac{\alpha_k}{d_k} - e^{-d_k}  \rgt) \mathbf{c}_k^\mathrm{out}\,\label{eq:segment-integral}, \\
  \begin{aligned}
  d_k &= \lft(t^{\mathrm{out}}_k-t^{\mathrm{in}}_k\rgt) \sigma_k \quad&\quad \alpha_k &= 1-e^{-d_k} \label{eq:segment-alpha} \\ \mathbf{c}_k^\mathrm{in} &= \mathbf{c}_k \lft(\ray\lft(t^{\mathrm{in}}_k\rgt)\rgt) \quad&\quad \mathbf{c}_k^\mathrm{out} &= \mathbf{c}_k \lft(\ray\lft(t^{\mathrm{out}}_k\rgt)\rgt)
  \end{aligned}
\end{gather}
To render
""".strip()
    out = expander.expand(text)
    out = [t for t in out if t.value != " " or t.value != "\n"]
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
