from typing import List, Optional, Tuple
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.utils import substitute_token_args
from latex2json.expander.macro_registry import Macro
from dataclasses import dataclass

from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import is_begin_group_token


@dataclass
class DefResult:
    name: str
    definition: List[Token]
    usage_pattern: List[Token]


def get_parsed_args_from_usage_pattern(
    expander: ExpanderCore, usage_pattern: List[Token]
) -> List[List[Token]]:
    parsed_args: List[List[Token]] = []

    N = len(usage_pattern)

    for i, pat in enumerate(usage_pattern):
        tok = expander.peek()
        if tok is None:
            return parsed_args

        if pat.type == TokenType.PARAMETER:
            # expects argument
            tokens = expander.parse_immediate_token()
            if tokens is None:
                expander.logger.warning(
                    f"Warning: expected an argument but found nothing"
                )
                return parsed_args

            # find the next literal
            next_literal_token = None
            if i + 1 < N and usage_pattern[i + 1].type == TokenType.CHARACTER:
                next_literal_token = usage_pattern[i + 1]

            if next_literal_token:
                tok = expander.peek()
                # if there is a next literal token, we keep consuming until we find it
                while tok and tok != next_literal_token:
                    tokens.append(expander.consume())
                    tok = expander.peek()

            index = int(pat.value) - 1
            # Extend parsed_args with empty lists if needed
            while len(parsed_args) <= index:
                parsed_args.append([])
            parsed_args[index] = tokens
            continue
        else:
            if tok == pat:
                expander.consume()
                continue
            else:
                expander.logger.warning(
                    f"Warning: expected {pat.value} but found {tok.value}"
                )
                return parsed_args

    return parsed_args


class DefMacro(Macro):
    def __init__(self, name: str, is_lazy=True, is_global=False):
        super().__init__(name)
        self.is_lazy = is_lazy
        self.is_global = is_global

        self.handler = lambda expander, node: self._expand(expander, node)

    def _expand(self, expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        out = def_handler(expander, token)
        if out is None:
            return None

        if not self.is_lazy:
            out.definition = expander.expand_tokens(out.definition)

        def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
            parsed_args = get_parsed_args_from_usage_pattern(
                expander, out.usage_pattern
            )
            subbed = substitute_token_args(out.definition, parsed_args, math_mode=False)
            expander.push_tokens(subbed)
            return []

        macro = Macro(out.name, handler, out.definition)
        expander.register_macro(out.name, macro, is_global=self.is_global)

        return []


def get_def_usage_pattern_and_definition(
    expander: ExpanderCore,
) -> Tuple[List[Token], List[Token]]:
    raw_usage_pattern_tokens: List[Token] = []

    raw_usage_pattern_tokens = expander.parse_tokens_until(
        lambda tok: is_begin_group_token(tok)
    )

    tok = expander.peek()
    if is_begin_group_token(tok):
        definition_tokens = expander.parse_brace_as_tokens()
        return raw_usage_pattern_tokens, definition_tokens

    return None, None


def def_handler(expander: ExpanderCore, token: Token) -> Optional[DefResult]:
    expander.skip_whitespace()
    cmd = expander.peek()
    if not cmd or cmd.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(
            f"Warning: \\def expects a command node, but found {cmd}"
        )
        return None

    expander.consume()

    name = cmd.value
    usage_pattern, definition = get_def_usage_pattern_and_definition(expander)

    if usage_pattern is None or definition is None:
        expander.logger.warning(
            f"Warning: \\def expects a proper usage pattern and definition"
        )
        return None

    return DefResult(
        name=name,
        definition=definition,
        usage_pattern=usage_pattern,
    )


def register_def(expander: ExpanderCore):
    expander.register_macro(
        "\\def", DefMacro("\\def", is_lazy=True, is_global=False), is_global=True
    )
    expander.register_macro(
        "\\edef", DefMacro("\\edef", is_lazy=False, is_global=False), is_global=True
    )
    expander.register_macro(
        "\\gdef", DefMacro("\\gdef", is_lazy=True, is_global=True), is_global=True
    )
    expander.register_macro(
        "\\xdef", DefMacro("\\xdef", is_lazy=False, is_global=True), is_global=True
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_def(expander)

    # expander.expand(r"\def\foo(e#1{BAR #1 BAR}")

    # text = r"\def\foo(e#1{BAR #1 BAR} \def\hi{HI}"
    # expander.expand(text)

    # out = expander.expand(r"\foo(e\hi")
    # # expected = expander.expand("BAR HI BAR")
    # print(out)

    text = r"""
    \def\foo{FOO}
    \def\bar{\foo}
    \def\foo{BAR}
    """.strip()

    expander.expand(text)
    print(expander.expand(r"\bar"))
