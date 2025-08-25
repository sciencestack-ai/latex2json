import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.types import EnvironmentType
from tests.expander.handlers.environment.test_environment_handlers import mock_env_token


def test_declaretheorem_basic():
    expander = Expander()

    # Test basic declaretheorem
    expander.expand(r"\declaretheorem{theorem}")
    assert expander.expand(
        r"\begin{theorem}This is a theorem\end{theorem}"
    ) == mock_env_token(
        expander,
        "theorem",
        content="This is a theorem",
        numbering="1",
        display_name="theorem",
        env_type=EnvironmentType.THEOREM,
    )


def test_declaretheorem_with_name():
    expander = Expander()

    # Test declaretheorem with custom name
    expander.expand(r"\declaretheorem[name=Theorem]{thm}")
    assert expander.expand(r"\begin{thm}This is a theorem\end{thm}") == mock_env_token(
        expander,
        "thm",
        content="This is a theorem",
        numbering="1",
        display_name="Theorem",
        env_type=EnvironmentType.THEOREM,
    )


def test_declaretheorem_unnumbered():
    expander = Expander()

    # Test unnumbered theorem
    expander.expand(r"\declaretheorem[numbered=no]{remark}")
    assert expander.expand(
        r"\begin{remark}This is a remark\end{remark}"
    ) == mock_env_token(
        expander,
        "remark",
        content="This is a remark",
        display_name="remark",
        env_type=EnvironmentType.THEOREM,
    )


def test_declaretheorem_sibling():
    expander = Expander()

    # Create base theorem and sibling
    expander.expand(r"\declaretheorem[name=Theorem]{thm}")
    expander.expand(r"\declaretheorem[name=Definition,sibling=thm]{defn}")

    # Test that they share counter
    expander.expand(r"\begin{thm}First theorem\end{thm}")
    assert expander.expand(r"\begin{defn}First definition\end{defn}") == mock_env_token(
        expander,
        "defn",
        content="First definition",
        numbering="2",
        display_name="Definition",
        env_type=EnvironmentType.THEOREM,
    )


def test_declaretheorem_sharecounter():
    expander = Expander()

    # Create base theorem and one with shared counter
    expander.expand(r"\declaretheorem[name=Theorem]{thm}")
    expander.expand(r"\declaretheorem[name=Lemma,sharecounter=thm]{lemma}")

    # Test that they share counter
    expander.expand(r"\begin{thm}First theorem\end{thm}")
    assert expander.expand(r"\begin{lemma}First lemma\end{lemma}") == mock_env_token(
        expander,
        "lemma",
        content="First lemma",
        numbering="2",
        display_name="Lemma",
        env_type=EnvironmentType.THEOREM,
    )


def test_declaretheorem_numberlike():
    expander = Expander()

    # Create base theorem and one with numberlike
    expander.expand(r"\declaretheorem[name=Theorem]{thm}")
    expander.expand(r"\declaretheorem[name=Corollary,numberlike=thm]{cor}")

    # Test that they share counter
    expander.expand(r"\begin{thm}First theorem\end{thm}")
    assert expander.expand(r"\begin{cor}First corollary\end{cor}") == mock_env_token(
        expander,
        "cor",
        content="First corollary",
        numbering="2",
        display_name="Corollary",
        env_type=EnvironmentType.THEOREM,
    )


def test_declaretheorem_numberwithin():
    expander = Expander()

    # Set up section counter
    expander.expand(r"\section{First Section}")

    # Create theorem with numberwithin
    expander.expand(r"\declaretheorem[name=Theorem,numberwithin=section]{thm}")

    assert expander.expand(r"\begin{thm}First theorem\end{thm}") == mock_env_token(
        expander,
        "thm",
        content="First theorem",
        numbering="1.1",
        display_name="Theorem",
        env_type=EnvironmentType.THEOREM,
    )


def test_declaretheorem_complex_example():
    expander = Expander()

    # Test the example from the main function
    text = r"""
\declaretheorem[name=Theorem,Refname={Theorem,Theorems}]{thm}
\declaretheorem[name=Definition,Refname={Definition,Definitions},sibling=thm]{defn}

\begin{thm}
    This is a theorem
\end{thm}

\begin{defn}
    This is a definition
\end{defn}
""".strip()

    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()

    # Verify the environments were created and numbered correctly
    assert r"\begin{thm}" in out_str
    assert r"\begin{defn}" in out_str
    assert "This is a theorem" in out_str
    assert "This is a definition" in out_str
