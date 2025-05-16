from copy import deepcopy
from typing import List, Optional, Tuple
from latex2json import expander
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.utils import substitute_args
from latex2json.expander.macro_registry import Macro
from latex2json.nodes import ASTNode, DefNode
from latex2json.nodes.syntactic_nodes import (
    ArgNode,
    BraceNode,
    BracketNode,
    CommandNode,
    TextNode,
)
from latex2json.nodes.utils import convert_bracket_node_to_literal_ast
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.catcodes import Catcode
from dataclasses import dataclass

from latex2json.tokens.types import TokenType


@dataclass
class DefResult:
    name: str
    definition: List[ASTNode]
    usage_pattern: List[ASTNode]
    depth: int = -1


def get_parsed_args_from_usage_pattern(
    expander: ExpanderCore, usage_pattern: List[ASTNode]
) -> List[ASTNode]:
    parsed_args: List[ASTNode] = []

    idx = 0
    n = len(usage_pattern)
    if n == 0:
        return []

    parser = expander.parser

    while idx < n:
        tok = parser.peek()
        if tok is None:
            return parsed_args

        pat = usage_pattern[idx]
        # literal text in the signature
        if isinstance(pat, TextNode):
            # should be single character node
            if tok.value == pat.text:
                parser.consume()
                idx += 1
                continue
            else:
                expander.logger.warning(
                    f"Warning: expected {pat.text} but found {tok.value}"
                )
                return parsed_args

        # match the args
        if isinstance(pat, ArgNode):
            ast = parser.parse_immediate_token()

            # if the arg is a brace or command, we simply add it
            if isinstance(ast, BraceNode) or isinstance(ast, CommandNode):
                parsed_args.append(ast)
                idx += 1
                continue

            if not isinstance(ast, TextNode):
                expander.logger.warning(
                    f"Warning: expected a text node but found {ast}"
                )
                return parsed_args

            # find the next TextNode literal
            next_lit = None
            for future in usage_pattern[idx + 1 :]:
                if isinstance(future, TextNode):
                    next_lit = future.text
                    break

            if not next_lit:
                # if there is no next literal, we just consume the next string literal as the arg
                parsed_args.append(ast)
                idx += 1
                continue

            # consume everything up until that literal
            buffer = ast.text
            tok = parser.peek()
            while tok:
                text = tok.value
                if text == next_lit:
                    parser.consume()
                    idx += 2
                    break
                buffer += text
                parser.consume()
                tok = parser.peek()
            if buffer:
                parsed_args.append(TextNode(buffer))
            continue

        if isinstance(pat, CommandNode):
            if tok and tok.type == TokenType.CONTROL_SEQUENCE:
                ast = parser.parse_command()
                if ast.name == pat.name:
                    idx += 1
                    continue

        # incomplete parse
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
            out.definition = expander.expand_nodes(out.definition)

        depth = out.depth

        def handler(
            expander: ExpanderCore, node: CommandNode
        ) -> Optional[List[ASTNode]]:
            definition = deepcopy(out.definition)
            parsed_args = get_parsed_args_from_usage_pattern(
                expander, out.usage_pattern
            )
            subbed = substitute_args(
                definition, parsed_args, depth=depth, math_mode=False
            )
            return subbed

        expander.register_handler(out.name, handler, is_global=self.is_global)

        return []


def get_def_usage_pattern_and_definition(
    parser: ParserCore,
) -> Tuple[List[ASTNode], List[ASTNode]]:
    raw_usage_pattern: List[ASTNode] = []

    node = parser.parse_element()
    while node and not isinstance(node, BraceNode):
        if isinstance(node, BracketNode):
            raw_usage_pattern.extend(convert_bracket_node_to_literal_ast(node))
        else:
            raw_usage_pattern.append(node)
        node = parser.parse_element()

    # break up usage pattern textnodes to single character nodes
    usage_pattern: List[ASTNode] = []
    for ele in raw_usage_pattern:
        if isinstance(ele, TextNode):
            usage_pattern.extend(ele.to_chars())
        else:
            usage_pattern.append(ele)

    if isinstance(node, BraceNode):
        definition = node.children
        return usage_pattern, definition

    return None, None


def def_handler(expander: ExpanderCore, node: CommandNode) -> Optional[DefResult]:
    parser = expander.parser

    expander.skip_whitespace()
    cmd = parser.parse_command()
    if not cmd:
        return None

    name = cmd.name
    usage_pattern, definition = get_def_usage_pattern_and_definition(parser)

    if usage_pattern is None or definition is None:
        expander.logger.warning(
            f"Warning: \\def expects a proper usage pattern and definition"
        )
        return None

    depth = -1
    for ele in usage_pattern:
        if isinstance(ele, ArgNode):
            depth = ele.depth
            break

    return DefResult(
        name=name,
        definition=definition,
        usage_pattern=usage_pattern,
        depth=depth,
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

    # expander.set_text(r"[HELLO:{sdsd}]")
    # usage_pattern = [
    #     TextNode("["),
    #     ArgNode(1, 1),
    #     TextNode(":"),
    #     ArgNode(2, 1),
    #     TextNode("]"),
    # ]
    # out = get_parsed_args_from_usage_pattern(expander, usage_pattern)
    # print(out)

    expander.set_text(r"{abc}a\cmd")
    usage_pattern = [
        ArgNode(1, 1),
        ArgNode(2, 1),
        ArgNode(3, 1),
    ]
    out = get_parsed_args_from_usage_pattern(expander, usage_pattern)
    print(out)
