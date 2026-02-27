import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.types import EnvironmentStartToken, EnvironmentType
from latex2json.tokens.utils import is_whitespace_token, strip_whitespace_tokens
from tests.expander.handlers.environment.test_environment_handlers import mock_env_token


def test_bracket_with_math_containing_bracket():
    """Test that ] inside $...$ doesn't prematurely close optional argument.

    e.g. \\begin{theorem}[Global regularity for $\\alpha\\in(2,3]$]
    The ] after 3 is inside math mode and should NOT close the optional arg.
    """
    from latex2json.parser.parser import Parser

    expander = Expander()
    parser = Parser(expander)
    expander.expand(r"\newtheorem{theorem}{Theorem}")

    text = r"\begin{theorem}[Global regularity for $\alpha\in(2,3]$]content\end{theorem}"
    nodes = parser.parse(text)

    assert len(nodes) == 1
    thm = nodes[0]
    assert thm.env_name == "theorem"
    assert thm.numbering == "1"

    # The title should contain the full optional arg including ] inside math
    title_json = [n.to_json() for n in thm.title]
    # Should have text + inline equation containing "2,3]"
    assert any(
        "2,3]" in str(n) for n in title_json
    ), f"Expected '2,3]' in title but got: {title_json}"

    # Body should be "content"
    body_json = [n.to_json() for n in thm.body]
    assert any("content" in str(n) for n in body_json)


def test_newtheorem():
    expander = Expander()

    # test standalone newtheorem
    expander.expand(r"\newtheorem{definition}{Definition}")
    assert expander.expand(r"\begin{definition}DEF\end{definition}") == mock_env_token(
        expander,
        "definition",
        content="DEF",
        numbering="1",
        display_name=expander.convert_str_to_tokens("Definition"),
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
        display_name=expander.convert_str_to_tokens("Remark"),
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
                display_name=expander.convert_str_to_tokens("Theorem"),
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
                display_name=expander.convert_str_to_tokens("Lemma"),
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


def test_named_theorem_patterns():
    expander = Expander()

    expander.expand(r"\theoremname{Theorem}")
    assert expander.expand(r"\theoremname") == expander.expand("Theorem")

    expander.expand(r"\proofname{Proof}")
    assert expander.expand(r"\proofname") == expander.expand("Proof")


def test_newtheorem_displayname():
    expander = Expander()

    text = r"""
\newtheorem{theorem}{Theorem}[chapter]
\newtheorem*{namedtheorem}{\theoremname}
\newcommand{\theoremname}{testing}

\newenvironment{named}[1]{ \renewcommand{\theoremname}{#1} \begin{namedtheorem}} {\end{namedtheorem}}
\begin{named}{Parseval's Theorem}
\end{named}
""".strip()

    out = expander.expand(text)
    out = [t for t in out if not is_whitespace_token(t)]
    assert len(out) > 1
    # test that \theoremname displayname is expanded at time of env creation
    expected_display_name = expander.convert_str_to_tokens("Parseval's Theorem")
    assert out[0] == EnvironmentStartToken("named")
    assert out[1] == EnvironmentStartToken(
        "namedtheorem",
        display_name=expected_display_name,
        env_type=EnvironmentType.THEOREM,
    )
