from latex2json.expander.expander import Expander
from latex2json.tokens.types import EnvironmentStartToken, Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens


def test_at_begin_end_document_handler():
    expander = Expander()
    text = r"""
    \def\aaa{AAA}

    \AtBeginDocument{\def\newaaa{\aaa}} % only expanded at begin document
    \AtEndDocument{END} % executed/returned right before the end document token
    \AtEndDocument{END2} % executed/returned right before the end document token

    \def\aaa{BBB}

    \begin{document}
    \newaaa % BBB
    \end{document}
""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out[0] == EnvironmentStartToken("document")
    assert out[-1] == Token(type=TokenType.ENVIRONMENT_END, value="document")

    body_tokens = out[1:-1]
    body_stripped = strip_whitespace_tokens(body_tokens)
    body_str = expander.convert_tokens_to_str(body_stripped)
    assert body_str.startswith("BBB")


def test_at_begin_document_defs_are_global():
    r"""Macros defined via \def inside \AtBeginDocument should persist
    across scope boundaries (matching real LaTeX top-level behavior)."""
    expander = Expander()
    text = r"""
    \makeatletter
    \AtBeginDocument{\def\@myinternalmacro{INTERNAL}}
    \makeatother

    \begin{document}
    {scoped text}
    \makeatletter
    \@myinternalmacro
    \makeatother
    \end{document}
""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    body_str = expander.convert_tokens_to_str(out)
    assert "INTERNAL" in body_str


def test_at_begin_document_conditional_def():
    r"""Macros defined inside conditionals within \AtBeginDocument should
    persist throughout the document body."""
    expander = Expander()
    text = r"""
    \makeatletter
    \newif\ifmyflag \myflagtrue
    \AtBeginDocument{%
        \ifmyflag
            \def\@myflagresult{FLAG-TRUE}%
        \else
            \def\@myflagresult{FLAG-FALSE}%
        \fi
    }
    \makeatother

    \begin{document}
    Before group.
    {inside group}
    After group.
    \makeatletter
    \@myflagresult
    \makeatother
    \end{document}
""".strip()
    out = expander.expand(text)
    body_str = expander.convert_tokens_to_str(out)
    assert "FLAG-TRUE" in body_str
