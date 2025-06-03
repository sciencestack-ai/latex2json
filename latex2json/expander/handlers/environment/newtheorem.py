from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.latex_maps.environments import EnvironmentDefinition
from latex2json.tokens.types import Token, TokenType


def newtheorem_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""
    \newtheorem{env_name}{display_name}
    \newtheorem{env_name}{display_name}[reset_counter]
    \newtheorem{env_name}[shared_counter]{display_name}
    """
    expander.parse_asterisk()
    env_name = expander.parse_brace_name()
    if env_name is None:
        expander.logger.warning(
            f"Warning: \\newtheorem expects an environment name, but found {token}"
        )
        return None

    expander.skip_whitespace()
    tok = expander.peek()
    if tok is None:
        return None

    counter_name = env_name
    has_shared_counter = False
    if tok.value == "[":
        shared_counter = expander.parse_brace_name(bracket=True)
        if not shared_counter:
            expander.logger.warning(
                f"Warning: {token} expects a shared counter, but found {expander.peek()}"
            )
            return None
        counter_name = shared_counter
        has_shared_counter = True
        expander.skip_whitespace()

        tok = expander.peek()

        if tok is None:
            return None

    # create new counter name
    expander.state.new_counter(counter_name)

    display_name = env_name
    if tok.value == "{":
        display_name = expander.parse_brace_name()
        if not display_name:
            expander.logger.warning(
                f"Warning: {token} expects a display name, but found {expander.peek()}"
            )
            return None
        expander.skip_whitespace()

        if not has_shared_counter:
            reset_counter = expander.parse_brace_name(bracket=True)
            if reset_counter:
                expander.state.counter_within(counter_name, reset_counter)

    env_def = EnvironmentDefinition(
        name=env_name,
        display_name=display_name,
        counter_name=counter_name,
        has_direct_command=False,
    )
    expander.register_environment(env_def, is_global=True)

    return []


def register_newtheorem(expander: ExpanderCore):
    r"""
    % Independent numbering
    \newtheorem{theorem}{Theorem}
    % Creates: Theorem 1, Theorem 2, Theorem 3, ...

    % Numbered within sections
    \newtheorem{proposition}{Proposition}[section]
    % Creates: Proposition 1.1, Proposition 1.2, Proposition 2.1, ...

    % Shared counter
    \newtheorem{theorem}{Theorem}
    \newtheorem{lemma}[theorem]{Lemma}
    % Creates: Theorem 1, Lemma 2, Theorem 3, Lemma 4, ...

    % Multiple styles
    \newtheorem{definition}{Definition}[section]
    \newtheorem{example}[definition]{Example}
    \newtheorem{remark}[definition]{Remark}
    % All share same counter within sections

    """
    expander.register_handler(
        "\\newtheorem",
        newtheorem_handler,
        is_global=True,
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_newtheorem(expander)

    # Basic theorem
    text = r"""
\newtheorem{theorem}{Theorem}[section]
\newtheorem{lemma}[theorem]{Lemma}

\section{Section 1}
\begin{theorem}This is a theorem\end{theorem} % 1.1
\begin{theorem}This is a theorem\end{theorem} % 1.2
\begin{lemma}This is a lemma\end{lemma} % 1.3
"""
    out = expander.expand(text)
    print(expander.expand(r"\value{theorem}"))  # 1.3

    # # Theorem with section numbering
    # expander.expand(r"\newtheorem{lemma}[section]{Lemma}")
    # print(expander.expand(r"\begin{lemma}This is a lemma\end{lemma}"))
