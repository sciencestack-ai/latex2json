from logging import Logger
from typing import Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.tokenizer import Tokenizer


class Expander(ExpanderCore):
    def __init__(
        self,
        tokenizer: Optional[Tokenizer] = None,
        logger: Logger = Logger("expander"),
    ):
        super().__init__(tokenizer, logger)

        self._init_primitives()

    def _init_primitives(self):
        # Define core TeX/LaTeX primitives in the base registry.
        # Primitives are defined using define_primitive which uses set(is_global=True)
        from latex2json.expander.handlers import register_handlers

        register_handlers(self)


if __name__ == "__main__":
    expander = Expander()

    text = r"""
    \count0=123
    \edef\foo{\count0}  % → literally expands to "\count0", NOT "123"
    \edef\bar{\the\count0}  % → expands to "123"
""".strip()
    expander.expand(text)
    out1 = expander.expand(r"\foo")
    out2 = expander.expand(r"\bar")
