from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.latex_maps.environments import (
    COMMON_ENVIRONMENTS,
)


def register_base_environment_handlers(expander: ExpanderCore):
    """Register basic environments that just wrap their content."""
    for env_name, env_def in COMMON_ENVIRONMENTS.items():
        expander.register_environment(env_def.copy())


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_base_environment_handlers(expander)

    text = r"""
    \counterwithin{equation}{section}

    \section{Section 1}
    \begin{equation}
    1+1
    \end{equation}

    \begin{equation*}
    1+1
    \end{equation*}
"""
    out = expander.expand(text)
    print(expander.state.get_counter_as_format("equation", hierarchy=True))
    # expander.expand(r"\newenvironment{test}[1]{BEGIN #1 123}{END}")
    # out = expander.expand(r"\begin{test}{ABC}CONTENT\end{test}")
