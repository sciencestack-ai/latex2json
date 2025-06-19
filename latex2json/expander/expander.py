from logging import Logger
from typing import Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.tokenizer import Tokenizer
from latex2json.tokens.utils import is_whitespace_token, strip_whitespace_tokens


class Expander(ExpanderCore):
    def __init__(
        self,
        tokenizer: Optional[Tokenizer] = None,
        logger: Optional[Logger] = None,
    ):
        super().__init__(tokenizer, logger)

        self._register_handlers_and_packages()

    def _register_handlers_and_packages(self):
        from latex2json.expander.handlers import register_handlers
        from latex2json.expander.packages import register_packages

        register_handlers(self)
        register_packages(self)


if __name__ == "__main__":
    expander = Expander()

    verbatim_env_tokens = expander.expand(
        r"\begin{verbatim}\newcommand{test}{123}\end {fake}##1\end{verbatim}"
    )

    # while not expander.eof():
    #     next_tokens = expander.next_non_expandable_tokens()
    #     if not next_tokens:
    #         break
    #     stripped = strip_whitespace_tokens(next_tokens)
    #     if stripped:
    #         print(stripped)
