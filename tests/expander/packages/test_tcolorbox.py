from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token


def test_newtcbox():
    expander = Expander()

    # rolls out to \tcbox[hello, title=default]{BOX}
    text = r"""
\newtcbox{\mymath}[1][default]{hello, title=#1}

    \mymath{BOX}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == r"\tcbox[hello, title=default]{BOX}"


def test_newtcolorbox_basic():
    """Test basic newtcolorbox with no arguments."""
    expander = Expander()
    text = r"""
\newtcolorbox{simplebox}{colback=red}

\begin{simplebox}
Content here.
\end{simplebox}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert r"\begin{simplebox}" in out_str
    assert "Content here." in out_str
    assert r"\end{simplebox}" in out_str


def test_newtcolorbox_with_args():
    """Test newtcolorbox with mandatory and optional arguments."""
    expander = Expander()
    text = r"""
\newtcolorbox{mybox}[2][]{colback=red, title=#2, #1}

\begin{mybox}[colback=yellow]{Hello there}
This is my box.
\end{mybox}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    # Arguments should be consumed, not appear in output
    assert r"\begin{mybox}" in out_str
    assert "This is my box." in out_str
    assert r"\end{mybox}" in out_str
    # The arguments [colback=yellow]{Hello there} should NOT appear
    assert "colback=yellow" not in out_str
    assert "Hello there" not in out_str


def test_newtcolorbox_two_mandatory_args():
    """Test newtcolorbox with two mandatory arguments."""
    expander = Expander()
    text = r"""
\newtcolorbox{myboxwithtwo}[2]{title=#1, subtitle=#2}

\begin{myboxwithtwo}{Title}{Subtitle}
Content.
\end{myboxwithtwo}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert r"\begin{myboxwithtwo}" in out_str
    assert "Content." in out_str
    # Arguments consumed
    assert "Title" not in out_str or "Subtitle" not in out_str


def test_declaretcolorbox_basic():
    """Test DeclareTColorBox with xparse arg spec."""
    expander = Expander()
    text = r"""
\DeclareTColorBox{mytotalbox}{O{}mO{-2mm}}{colback=red, title=#2}

\begin{mytotalbox}{My Title}
Content here.
\end{mytotalbox}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert r"\begin{mytotalbox}" in out_str
    assert "Content here." in out_str
    assert r"\end{mytotalbox}" in out_str


def test_declaretcolorbox_all_args():
    """Test DeclareTColorBox with all arguments provided."""
    expander = Expander()
    text = r"""
\DeclareTColorBox{mytotalbox}{O{}mO{-2mm}}{title=#2}

\begin{mytotalbox}[opt1]{Mandatory}[-5mm]
Box content.
\end{mytotalbox}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert r"\begin{mytotalbox}" in out_str
    assert "Box content." in out_str


def test_newtcolorbox_registers_environment():
    """Test that newtcolorbox properly registers the environment."""
    expander = Expander()
    text = r"\newtcolorbox{testenv}[1]{title=#1}"
    expander.expand(text)

    # Check that environment is registered
    env_def = expander.get_environment_definition("testenv")
    assert env_def is not None
    assert env_def.name == "testenv"
    assert env_def.num_args == 1


def test_declaretcolorbox_registers_environment():
    """Test that DeclareTColorBox properly registers the environment."""
    expander = Expander()
    text = r"\DeclareTColorBox{declaredenv}{O{}mm}{options}"
    expander.expand(text)

    # Check that environment is registered
    env_def = expander.get_environment_definition("declaredenv")
    assert env_def is not None
    assert env_def.name == "declaredenv"
    assert env_def.num_args == 3  # O{} + m + m


def test_renewtcolorbox():
    """Test that renewtcolorbox works."""
    expander = Expander()
    text = r"""
\newtcolorbox{mybox}{colback=red}
\renewtcolorbox{mybox}[1]{colback=blue, title=#1}

\begin{mybox}{New Title}
Content.
\end{mybox}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert r"\begin{mybox}" in out_str
    assert "Content." in out_str
