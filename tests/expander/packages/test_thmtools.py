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


def test_restatable_basic():
    """Test basic restatable: registers macro and expands correctly with proper numbering."""
    expander = Expander()
    expander.expand(r"\declaretheorem[name=Theorem]{theorem}")

    # Test basic restatable
    text = r"""
\begin{restatable}[Main Property]{theorem}{MainResult}
Content here
\end{restatable}
""".strip()
    out = expander.expand(text)

    # Check that original expansion produces numbered theorem
    assert out[0] == mock_env_token(
        expander, "theorem", "", numbering="1",
        display_name="Theorem", env_type=EnvironmentType.THEOREM
    )[0]
    assert "Content here" in expander.convert_tokens_to_str(out)

    # Test that \MainResult macro was registered and can be called
    result = expander.expand(r"\MainResult")
    # Should produce numbered theorem (numbering continues: 2)
    assert result[0] == mock_env_token(
        expander, "theorem", "", numbering="2",
        display_name="Theorem", env_type=EnvironmentType.THEOREM
    )[0]
    assert "Content here" in expander.convert_tokens_to_str(result)


def test_restatable_starred():
    r"""Test restatable*: starred version reuses current numbering without incrementing.

    LIMITATION: In real LaTeX, \MainResult* should reference the final numbering from
    the last occurrence in the document. Our implementation shows the current counter
    state at the time of call, which is a limitation of single-pass architecture.
    """
    expander = Expander()
    expander.expand(r"\declaretheorem[name=Theorem]{theorem}")

    # Create a restatable* (starred environment doesn't increment counter)
    text = r"""
\begin{restatable*}[Key]{theorem}{KeyResult}
Important result
\end{restatable*}
""".strip()
    out = expander.expand(text)

    # Should produce numbered theorem with "1" (capped at 1 to avoid "Theorem 0")
    assert out[0] == mock_env_token(
        expander, "theorem", "",
        numbering="1",  # Capped at 1 minimum
        display_name="Theorem", env_type=EnvironmentType.THEOREM
    )[0]

    # Now increment counter with a regular theorem
    expander.expand(r"\begin{theorem}Regular theorem\end{theorem}")

    # Test that \KeyResult* doesn't increment counter (shows current: 1)
    result_star = expander.expand(r"\KeyResult*")
    assert result_star[0] == mock_env_token(
        expander, "theorem", "",
        numbering="1",  # Shows current counter state (1 after one theorem)
        display_name="Theorem", env_type=EnvironmentType.THEOREM
    )[0]

    # Test that \KeyResult without asterisk increments counter (shows 2)
    result_no_star = expander.expand(r"\KeyResult")
    assert result_no_star[0] == mock_env_token(
        expander, "theorem", "",
        numbering="2",  # Counter incremented
        display_name="Theorem", env_type=EnvironmentType.THEOREM
    )[0]


def test_restatable_macro_captures_tokens():
    """Test that restatable captures tokens literally, preserving unexpanded macros."""
    expander = Expander()
    expander.expand(r"\declaretheorem[name=Theorem]{theorem}")
    expander.expand(r"\def\xxx{XXX}")

    # Create restatable that uses the macro
    text = r"""
\begin{restatable}{theorem}{SampleThm}
Text with \xxx
\end{restatable}
""".strip()
    expander.expand(text)

    # Redefine the macro
    expander.expand(r"\def\xxx{YYY}")

    # Call the restatable - tokens are preserved as captured
    result = expander.expand(r"\SampleThm")
    result_str = expander.convert_tokens_to_str(result)

    # The macro tokens are preserved literally (not expanded at capture or call time)
    assert r"\xxx" in result_str
