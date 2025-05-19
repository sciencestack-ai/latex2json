from dataclasses import dataclass
from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import Token, TokenType


@dataclass
class LetResult:
    name: str
    definition: List[Token]


class LetMacro(Macro):
    def __init__(self, name: str):
        super().__init__(name)
        self.handler = lambda expander, node: self._expand(expander, node)

    def _expand(self, expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        out = let_handler(expander, token)
        if out is None:
            return None

        def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
            expander.stream.push_tokens(out.definition)
            return []

        macro = Macro(out.name, handler, out.definition)
        expander.register_macro(out.name, macro, is_global=False)

        return []


def let_handler(expander: ExpanderCore, token: Token) -> Optional[LetResult]:
    expander.skip_whitespace()
    cmd = expander.peek()
    if not cmd or cmd.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(
            f"Warning: \\let expects a command node, but found {cmd}"
        )
        return None

    expander.consume()

    name = cmd.value

    expander.skip_whitespace()
    expander.parse_equals()
    definition = expander.consume()

    if not definition:
        expander.logger.warning(
            f"Warning: \\let expects a definition, but found {definition}"
        )
        return None

    # copies the definition as is, without expanding it
    final_definition = expander.convert_to_macro_definitions([definition])

    return LetResult(
        name=name,
        definition=final_definition,
    )


def register_let(expander: ExpanderCore):
    expander.register_macro(
        "\\let",
        LetMacro("\\let"),
        is_global=True,
    )


if __name__ == "__main__":
    expander = ExpanderCore()
    register_let(expander)
    expander.expand(r"\let\foo=3")
    expander.expand(r"\foo")
