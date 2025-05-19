from logging import Logger
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.tokenizer import Tokenizer


class Expander(ExpanderCore):
    def __init__(
        self,
        tokenizer: Tokenizer = Tokenizer(),
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
    \def\foo#1{
        \def\bar##1{BAR #1 ##1}
        \gdef\barx{\bar{BRO}}
    }
""".strip()
    expander.set_text(text)
    print(expander.process())
