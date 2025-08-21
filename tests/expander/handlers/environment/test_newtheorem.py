import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.types import EnvironmentType
from tests.expander.handlers.environment.test_environment_handlers import mock_env_token


def test_newtheorem():
    expander = Expander()

    # test standalone newtheorem
    expander.expand(r"\newtheorem{definition}{Definition}")
    assert expander.expand(r"\begin{definition}DEF\end{definition}") == mock_env_token(
        expander,
        "definition",
        content="DEF",
        numbering="1",
        display_name="Definition",
        env_type=EnvironmentType.THEOREM,
    )

    # check that \the... counter is created
    assert expander.convert_tokens_to_str(expander.expand(r"\thedefinition")) == "1"

    # test unnumbered with asterisk
    expander.expand(r"\newtheorem*{remark}{Remark}")
    assert expander.expand(r"\begin{remark}REM\end{remark}") == mock_env_token(
        expander,
        "remark",
        content="REM",
        display_name="Remark",
        env_type=EnvironmentType.THEOREM,
    )

    # test with shared and nested counters
    text = r"""
\newtheorem{theorem}{Theorem}[section]
\newtheorem{lemma}[theorem]{Lemma} % shared counter with theorem

\section{Section 1}
\begin{theorem}This is a theorem\end{theorem} % 1.1
\begin{theorem}This is a theorem\end{theorem} % 1.2
\begin{lemma}This is a lemma\end{lemma} % 1.3
"""
    out = expander.expand(text)
    assert expander.expand(r"\value{theorem}") == expander.expand("1.3")

    # with section, resets the counter
    expander.expand(r"\section{Section 2}")

    text_env_pairs = [
        (
            r"\begin{theorem}This is a theorem\end{theorem}",
            mock_env_token(
                expander,
                "theorem",
                content="This is a theorem",
                numbering="2.1",
                display_name="Theorem",
                env_type=EnvironmentType.THEOREM,
            ),
        ),
        (
            r"\begin{lemma}This is a lemma\end{lemma}",
            mock_env_token(
                expander,
                "lemma",
                content="This is a lemma",
                numbering="2.2",
                display_name="Lemma",
                env_type=EnvironmentType.THEOREM,
            ),
        ),
    ]

    for text, env_token in text_env_pairs:
        assert expander.expand(text) == env_token


def test_ignore_theorem_formatting():
    expander = Expander()

    # parsed and ignored
    text = r"""
\newtheoremstyle{mystyle}
  {}
  {}
  {\itshape}
  {}
  {\bfseries}
  {.}
  { }
  {\thmname{#1}\thmnumber{ #2}\thmnote{ (#3)}} POST""".strip()

    out = expander.expand(text)
    assert out == expander.expand(" POST")

    assert expander.expand(r"\theoremstyle{mystyle}") == []
