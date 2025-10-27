from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.environment.environment_utils import (
    begin_environment_handler,
    end_environment_handler,
)
from latex2json.tokens.types import Token


def begin_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    return begin_environment_handler(expander, token)


def end_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    return end_environment_handler(expander, token)


def register_begin_end(expander: ExpanderCore):
    expander.register_handler("\\begin", begin_handler, is_global=True)
    expander.register_handler("\\end", end_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    expander.expand(r"\newenvironment{env}[1]{START #1}{END}")
    out = expander.expand(r"\begin{env}{ARG1}TEST\end{env}")
