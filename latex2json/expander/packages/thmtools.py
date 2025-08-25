from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token
from latex2json.latex_maps.environments import EnvironmentDefinition
from latex2json.tokens.types import EnvironmentType
from typing import Dict, Optional, List

from latex2json.utils.tex_utils import parse_key_val_string


def declaretheorem_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    options = expander.parse_bracket_as_tokens()
    expander.skip_whitespace()
    env_name = expander.parse_brace_name()
    if not env_name:
        expander.logger.warning(
            f"Warning: \\declaretheorem expects an environment name"
        )
        return None

    options_str = expander.convert_tokens_to_str(options) if options else ""

    parsed_options = parse_key_val_string(options_str)

    display_name = parsed_options.get("name", env_name)
    counter_name = env_name

    numbered = True
    if "numbered" in parsed_options and parsed_options["numbered"] == "no":
        numbered = False

    if numbered:
        if "sibling" in parsed_options:
            counter_name = parsed_options["sibling"]
        elif "sharecounter" in parsed_options:
            counter_name = parsed_options["sharecounter"]
        elif "numberlike" in parsed_options:
            counter_name = parsed_options["numberlike"]
        elif "numberwithin" in parsed_options:
            expander.state.new_counter(counter_name)
            expander.state.counter_within(counter_name, parsed_options["numberwithin"])
        else:
            expander.state.new_counter(counter_name)
    else:
        counter_name = None

    # # Handle Refname (reference name for theorem)
    # if "Refname" in parsed_options:
    #     value = parsed_options["Refname"]

    env_def = EnvironmentDefinition(
        name=env_name,
        display_name=display_name,
        counter_name=counter_name,
        has_direct_command=False,
        env_type=EnvironmentType.THEOREM,
    )
    expander.register_environment(
        env_name, env_def, is_global=True, is_user_defined=True
    )

    return []


def register_thmtools(expander: ExpanderCore):
    expander.register_handler("declaretheorem", declaretheorem_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_thmtools(expander)

    text = r"""
\declaretheorem[name=Theorem,Refname={Theorem,Theorems}]{thm}
\declaretheorem[name=Definition,Refname={Definition,Definitions},sibling=thm]{defn}

\begin{thm} % numbering: 1
    This is a theorem
\end{thm}

\begin{defn} % numbering: 2
    This is a definition
\end{defn}

""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
