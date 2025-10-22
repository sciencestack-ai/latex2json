from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.latex_maps.environments import LIST_ENVIRONMENTS, EnvironmentDefinition
from latex2json.tokens.types import EnvironmentType, Token


def newlist_handler(expander: ExpanderCore, token: Token):
    blocks = expander.parse_braced_blocks(N_blocks=3, expand=True)

    if len(blocks) != 3:
        expander.logger.warning(
            "\\newlist: expected 3 blocks, got %d blocks", len(blocks)
        )
        return None

    new_env_name, env_type, _ = blocks
    new_env_name = expander.convert_tokens_to_str(new_env_name)
    env_type = expander.convert_tokens_to_str(env_type)
    ori_env_def = LIST_ENVIRONMENTS.get(env_type)
    if not ori_env_def:
        # default to enumerate?
        env_def = EnvironmentDefinition(
            "enumerate", num_args=1, default_arg=[], env_type=EnvironmentType.LIST
        )
        expander.logger.info(
            r"\newlist: unknown environment type %s, defaulting to 'enumerate'",
            env_type,
        )
    else:
        env_def = ori_env_def.copy()
    expander.register_environment(
        new_env_name, env_def, is_global=True, is_user_defined=True
    )
    return []


def register_enumitem(expander: ExpanderCore):
    expander.register_handler("newlist", newlist_handler, is_global=True)

    ignore_patterns = {"setlist": "*[{"}
    register_ignore_handlers_util(expander, ignore_patterns)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_enumitem(expander)

    text = r"""

\newlist{inlinelist}{itemize*}{1}
\setlist[inlinelist,1]{label=(\roman*)} % ignored
\begin{inlinelist}
    \item Item 1
    \item Item 2
\end{inlinelist}
""".strip()
    out = expander.expand(text)
