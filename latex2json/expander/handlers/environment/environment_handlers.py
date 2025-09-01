from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.latex_maps.environments import (
    COMMON_ENVIRONMENTS,
)
from latex2json.tokens.types import Token


def floatname_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    env_name = expander.parse_brace_name()
    if env_name is None:
        expander.logger.warning(f"\\floatname: Missing environment name")
        return None
    display_name = expander.parse_brace_name()
    if display_name is None:
        expander.logger.warning(f"\\floatname: Missing display name")
        return None

    env_def = expander.get_environment_definition(env_name)
    if env_def is None:
        # expander.logger.warning(f"\\floatname: Unknown environment {env_name}")
        return None
    env_def.display_name = display_name
    return []


def register_base_environment_handlers(expander: ExpanderCore):
    """Register basic environments that just wrap their content."""
    for env_name, env_def in COMMON_ENVIRONMENTS.items():
        env_def_instance = env_def.copy()
        if env_name == "subequations":

            def insubequation():
                expander.state.set_in_subequations(True)
                return []

            def outsubequation():
                expander.state.set_in_subequations(False)
                return []

            env_def_instance.hooks.begin.append(
                insubequation,
            )
            env_def_instance.hooks.end.append(
                outsubequation,
            )
        elif env_name in ["appendices", "appendix"]:

            def inappendices():
                expander.state.set_is_appendix(True)
                return []

            def outappendices():
                expander.state.set_is_appendix(False)
                return []

            env_def_instance.hooks.begin.append(
                inappendices,
            )
            env_def_instance.hooks.end.append(
                outappendices,
            )

        expander.register_environment(env_name, env_def_instance)
    expander.register_handler("floatname", floatname_handler, is_global=True)

    # table stuff to ignore?
    ignored_env_pattern_N_blocks = {
        "newcolumntype": "{[{",
        "columncolor": 1,  # Column colors
        "rowcolor": 1,  # Row colors
    }

    register_ignore_handlers_util(expander, ignored_env_pattern_N_blocks)


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
    \newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}
    """.strip()
    out = expander.expand(text)
    # print(expander.state.get_counter_as_format("equation", hierarchy=True))
    # expander.expand(r"\newenvironment{test}[1]{BEGIN #1 123}{END}")
    # out = expander.expand(r"\begin{test}{ABC}CONTENT\end{test}")
