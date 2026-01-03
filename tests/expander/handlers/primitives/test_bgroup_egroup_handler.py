import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import (
    BEGIN_BRACE_TOKEN,
    END_BRACE_TOKEN,
    TokenType,
)
from tests.test_utils import assert_token_sequence


def test_bgroup_egroup():
    expander = Expander()

    # scoped
    out = expander.expand("\\bgroup")  # -> evals to {
    assert_token_sequence(out, [BEGIN_BRACE_TOKEN])

    # test catcode change (local inside scope)
    assert expander.get_catcode(ord("@")) == Catcode.OTHER
    expander.makeatletter()
    assert expander.get_catcode(ord("@")) == Catcode.LETTER

    out = expander.expand("\\egroup")  # -> evals to }
    assert_token_sequence(out, [END_BRACE_TOKEN])

    assert expander.get_catcode(ord("@")) == Catcode.OTHER

    # begin/endgroup

    out = expander.expand(r"\begingroup")  # -> pushes scope but not {
    assert_token_sequence(out, [BEGIN_BRACE_TOKEN])

    # test catcode change (local inside scope)
    expander.makeatletter()
    assert expander.get_catcode(ord("@")) == Catcode.LETTER

    out = expander.expand(r"\endgroup")
    assert_token_sequence(out, [END_BRACE_TOKEN])

    assert expander.get_catcode(ord("@")) == Catcode.OTHER


def test_aftergroup():
    expander = Expander()

    # simple case
    out = expander.expand(r"\begingroup \aftergroup A B\endgroup")
    out_str = expander.convert_tokens_to_str(out).replace(" ", "")
    out_str = out_str.replace("{", "").replace("}", "")
    assert out_str == "BA"

    ## more complex case
    text = r"""
\newcommand\lft{\mathopen{}\left}
\newcommand\rgt{\aftergroup\mathclose\aftergroup{\aftergroup}\right}

\begin{gather}
  \mathbf{\Delta C}_k = 
  \lft( 1 - \frac{\alpha_k}{d_k} \rgt) \mathbf{c}_k^\mathrm{in} + 
  \lft( \frac{\alpha_k}{d_k} - e^{-d_k}  \rgt) \mathbf{c}_k^\mathrm{out}\,\label{eq:segment-integral}, \\
  \begin{aligned}
  d_k &= \lft(t^{\mathrm{out}}_k-t^{\mathrm{in}}_k\rgt) \sigma_k \quad&\quad \alpha_k &= 1-e^{-d_k} \label{eq:segment-alpha} \\ \mathbf{c}_k^\mathrm{in} &= \mathbf{c}_k \lft(\ray\lft(t^{\mathrm{in}}_k\rgt)\rgt) \quad&\quad \mathbf{c}_k^\mathrm{out} &= \mathbf{c}_k \lft(\ray\lft(t^{\mathrm{out}}_k\rgt)\rgt)
  \end{aligned}
\end{gather}
To render
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()

    # check that the gather environment is properly closed
    # and that end text "To render" does not wrongly contain a aftergroup boundary
    assert out_str.replace("\n", "").endswith("\\end{gather}To render")
    assert out_str.startswith("\\begin{gather}")
