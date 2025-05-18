from copy import deepcopy
from inspect import stack
from typing import List, Optional, Tuple
from latex2json import expander
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.utils import substitute_args, substitute_token_args
from latex2json.expander.macro_registry import Macro
from latex2json.nodes import ASTNode, DefNode
from latex2json.nodes.syntactic_nodes import (
    ArgNode,
    CommandNode,
)
from dataclasses import dataclass

from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, Token, TokenType


@dataclass
class DefResult:
    name: str
    definition: List[Token]
    usage_pattern: List[Token]
    depth: int = -1


def get_parsed_args_from_usage_pattern(
    expander: ExpanderCore, usage_pattern: List[Token]
) -> List[List[Token]]:
    parsed_args: List[List[Token]] = []

    parser = expander.parser

    N = len(usage_pattern)

    for i, pat in enumerate(usage_pattern):
        tok = parser.peek()
        if tok is None:
            return parsed_args

        if pat.type == TokenType.PARAMETER:
            # expects argument
            tokens = parser.parse_immediate_token()
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
                tok = parser.peek()
                # if there is a next literal token, we keep consuming until we find it
                while tok and tok != next_literal_token:
                    tokens.append(parser.consume())
                    tok = parser.peek()

            index = int(pat.value) - 1
            # Extend parsed_args with empty lists if needed
            while len(parsed_args) <= index:
                parsed_args.append([])
            parsed_args[index] = tokens
            continue
        else:
            if tok == pat:
                parser.consume()
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

    def _expand(
        self, expander: ExpanderCore, node: CommandNode
    ) -> Optional[List[ASTNode]]:
        out = def_handler(expander, node)
        if out is None:
            return None

        if not self.is_lazy:
            raise NotImplementedError("Eager expansion not implemented")
            out.definition = expander.expand_nodes(out.definition)
        # depth = out.depth

        def handler(
            expander: ExpanderCore, node: CommandNode
        ) -> Optional[List[ASTNode]]:
            parsed_args = get_parsed_args_from_usage_pattern(
                expander, out.usage_pattern
            )
            subbed = substitute_token_args(out.definition, parsed_args, math_mode=False)
            expander.parser.stream.push_tokens(subbed)
            return []

        expander.register_handler(out.name, handler, is_global=self.is_global)

        return []


def get_def_usage_pattern_and_definition(
    expander: ExpanderCore,
) -> Tuple[List[Token], List[Token]]:
    parser = expander.parser
    raw_usage_pattern_tokens: List[Token] = []

    tok = parser.peek()
    while tok and tok != BEGIN_BRACE_TOKEN:
        if tok.catcode == Catcode.PARAMETER:
            param_token = parser.parse_parameter_token()
            if param_token:
                raw_usage_pattern_tokens.append(param_token)
        else:
            raw_usage_pattern_tokens.append(tok)
            parser.consume()
        tok = parser.peek()

    if tok == BEGIN_BRACE_TOKEN:
        definition_tokens = parser.parse_brace_as_tokens()
        return raw_usage_pattern_tokens, definition_tokens

    return None, None


def def_handler(expander: ExpanderCore, node: CommandNode) -> Optional[DefResult]:
    expander.skip_whitespace()
    cmd = expander.parser.parse_element()
    if not isinstance(cmd, CommandNode):
        expander.logger.warning(
            f"Warning: \\def expects a command node, but found {cmd}"
        )
        return None

    name = cmd.name
    usage_pattern, definition = get_def_usage_pattern_and_definition(expander)

    if usage_pattern is None or definition is None:
        expander.logger.warning(
            f"Warning: \\def expects a proper usage pattern and definition"
        )
        return None

    # depth = -1
    # for ele in usage_pattern:
    #     if isinstance(ele, ArgNode):
    #         depth = ele.depth
    #         break

    return DefResult(
        name=name,
        definition=definition,
        usage_pattern=usage_pattern,
        # depth=depth,
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
    # print(expander.expand(r"\edef\test[#1:#2]{test #1:#2 ENDTEST}\test[HELLO:world]"))

    # text = r"\def\test[[#1:#2]{T #1:#2 ENDT}"
    # expander.set_text(text)

    # assert expander.parser.parse_command() == CommandNode(r"\def")
    # assert expander.parser.parse_command() == CommandNode(r"\test")

    # usage_pattern, definition = get_def_usage_pattern_and_definition(expander)
    # print(usage_pattern)

    expander.set_text(r"[[HI:{123}\cmd]")
    usage_pattern = [
        Token(TokenType.CHARACTER, "[", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, "[", catcode=Catcode.OTHER),
        Token(TokenType.PARAMETER, "1"),
        Token(TokenType.CHARACTER, ":", catcode=Catcode.OTHER),
        Token(TokenType.PARAMETER, "2"),
        Token(TokenType.CHARACTER, "]", catcode=Catcode.OTHER),
    ]
    out = get_parsed_args_from_usage_pattern(expander, usage_pattern)
