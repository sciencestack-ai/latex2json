from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.latex_maps.environments import (
    COMMON_ENVIRONMENTS,
)
from latex2json.tokens.types import Token


def floatname_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    env_name = expander.parse_brace_name()
    if env_name is None:
        expander.logger.warning(f"Warning: \\floatname: Missing environment name")
        return None
    display_name = expander.parse_brace_name()
    if display_name is None:
        expander.logger.warning(f"Warning: \\floatname: Missing display name")
        return None

    env_def = expander.get_environment_definition(env_name)
    if env_def is None:
        # expander.logger.warning(f"Warning: \\floatname: Unknown environment {env_name}")
        return None
    env_def.display_name = display_name
    return []


def register_base_environment_handlers(expander: ExpanderCore):
    """Register basic environments that just wrap their content."""
    for env_name, env_def in COMMON_ENVIRONMENTS.items():
        expander.register_environment(env_def.copy())

    expander.register_handler("floatname", floatname_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_base_environment_handlers(expander)

    #     text = r"""
    #     \counterwithin{equation}{section}

    #     \section{Section 1}
    #     \begin{equation}
    #     1+1
    #     \end{equation}

    #     \begin{equation*}
    #     1+1
    #     \end{equation*}
    # """
    text = r"""
    \begin{figure}[htb]Content\end{figure}
    """.strip()
    out = expander.expand(text)
    # print(expander.state.get_counter_as_format("equation", hierarchy=True))
    # expander.expand(r"\newenvironment{test}[1]{BEGIN #1 123}{END}")
    # out = expander.expand(r"\begin{test}{ABC}CONTENT\end{test}")
