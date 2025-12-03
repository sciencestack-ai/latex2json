import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.types import EnvironmentStartToken, Token, TokenType
from latex2json.tokens.utils import is_whitespace_token, strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def get_environment_tokens(expander: Expander, env_name: str, text: str):
    out_text = expander.expand(text)
    return [
        EnvironmentStartToken(env_name),
        *out_text,
        Token(TokenType.ENVIRONMENT_END, env_name),
    ]


def test_basic_newenvironment():
    expander = Expander()

    # Basic command without arguments
    text = r"""
    \newenvironment*{hello} {HELLO} {BYE}
    """.strip()
    expander.expand(text)
    assert expander.get_macro("\\hello")
    assert expander.get_macro("\\endhello")

    out = expander.expand(r"\hello MIDDLE \endhello")
    assert_token_sequence(
        out, get_environment_tokens(expander, "hello", "HELLO MIDDLE BYE")
    )

    # test only partial
    out = expander.expand(r"\hello")
    assert_token_sequence(
        out, [EnvironmentStartToken("hello")] + expander.expand("HELLO")
    )

    out = expander.expand(r"\endhello")
    assert_token_sequence(
        out, expander.expand("BYE") + [Token(TokenType.ENVIRONMENT_END, "hello")]
    )

    # requires begin_end to be registered
    out = expander.expand(r"\begin{hello} MIDDLE \end{hello}")
    assert_token_sequence(
        out, get_environment_tokens(expander, "hello", "HELLO MIDDLE BYE")
    )


def test_environment_with_args():
    expander = Expander()

    text = r"""
    \newenvironment {hello}[2][default]{HELLO #1 THERE #2}{BYE}
    """.strip()
    expander.expand(text)

    out = expander.expand(r"\hello {BRO}MIDDLE\endhello")
    assert_token_sequence(
        out,
        get_environment_tokens(expander, "hello", "HELLO default THERE BROMIDDLEBYE"),
    )

    # check with malformed brace
    out = expander.expand(r"\hello [new]{BRO}{MIDDLE \endhello")
    assert_token_sequence(
        out, get_environment_tokens(expander, "hello", "HELLO new THERE BRO{MIDDLE BYE")
    )

    # requires begin_end to be registered
    out = expander.expand(r"\begin{hello}[newdefault] {BROX} MIDDLE \end{hello}")
    assert_token_sequence(
        out,
        get_environment_tokens(
            expander, "hello", "HELLO newdefault THERE BROX MIDDLE BYE"
        ),
    )


def test_nested_environments():
    expander = Expander()

    text = r"""
\newenvironment{test}[1]{START TEST\newenvironment{innertest}[1]{Begin #1 ##1}{END #1}}{FINAL}
\test {333}\innertest{444}\endinnertest\endtest POST
    """.strip()
    out = expander.expand(text)
    strip_whitespace_tokens(out)

    expected = [
        EnvironmentStartToken("test"),
        *expander.expand("START TEST"),
        EnvironmentStartToken("innertest"),
        *expander.expand("Begin 333 444"),
        *expander.expand("END 333"),
        Token(TokenType.ENVIRONMENT_END, "innertest"),
        *expander.expand("FINAL"),
        Token(TokenType.ENVIRONMENT_END, "test"),
        *expander.expand(" POST"),
    ]
    assert_token_sequence(out, expected)


def test_newenvironment_with_specialchars():
    expander = Expander()

    text = r"""
    \newenvironment{ 1337 }{HELLO}{BYE}
    """.strip()
    expander.expand(text)
    # special char environments are valid but not registered as macros
    assert not expander.get_macro("\\1337")
    assert not expander.get_macro("\\end1337")

    # space sensitive!
    assert expander.state.get_environment_definition(" 1337 ")
    assert not expander.state.get_environment_definition("1337")

    out = expander.expand(r"\begin{ 1337 } MIDDLE \end{ 1337 }")
    assert_token_sequence(
        out, get_environment_tokens(expander, " 1337 ", "HELLO MIDDLE BYE")
    )

    # space sensitive! this will not work
    out = expander.expand(r"\begin{1337} MIDDLE \end{1337}")
    assert not expander.check_tokens_equal(
        out, get_environment_tokens(expander, "1337", "HELLO MIDDLE BYE")
    )


def test_newenvironment_with_counter():
    expander = Expander()

    text = r"""
    \newcounter{myenv}
    \newenvironment{myenv}{\stepcounter{myenv}}{}
    """.strip()
    out = expander.expand(text)
    assert expander.state.get_counter_value("myenv") == 0

    out = expander.expand(r"\begin{myenv}Hello\end{myenv}")
    assert out[0] == EnvironmentStartToken("myenv")
    assert expander.state.get_counter_value("myenv") == 1

    out = expander.expand(r"\begin{myenv}Hello\end{myenv}")
    assert out[0] == EnvironmentStartToken("myenv")
    assert expander.state.get_counter_value("myenv") == 2


def test_newenvironment_with_nested_begin_block():
    # Allow abstract environment to be redefined for this test
    expander = Expander(whitelisted_environments=[])

    text = r"""
\renewenvironment{abstract}%
{%
  \begin{quote}
}
{
  \end{quote}%
}

\begin{abstract}
ABSTRACT
\end{abstract}
""".strip()
    out = expander.expand(text)
    out = [t for t in out if not is_whitespace_token(t)]
    assert out[0] == EnvironmentStartToken("abstract")
    assert out[1] == EnvironmentStartToken("quote")
    assert out[2:-2] == expander.expand("ABSTRACT")
    assert out[-2] == Token(TokenType.ENVIRONMENT_END, "quote")
    assert out[-1] == Token(TokenType.ENVIRONMENT_END, "abstract")


def test_newenvironment_scoping():
    expander = Expander()

    text = r"""
\def\xx{MY XXX}
\renewenvironment{test}{
\let\xxx=\xx % in scope!
}
{
  \xxx % in scope! evals to "MY XXX"
}

\begin{test}
inner
\end{test}
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out[0] == EnvironmentStartToken("test")
    assert out[-1] == Token(TokenType.ENVIRONMENT_END, "test")
    body = strip_whitespace_tokens(out[1:-1])
    body_str = expander.convert_tokens_to_str(body)
    assert body_str.startswith("inner")
    assert body_str.endswith("MY XXX")

    assert not expander.get_macro("xxx")  # no longer in scope!


def test_newenviron_basic():
    expander = Expander()

    text = r"""
\def\xxx{XXX}
\NewEnviron{ack}{%
  \xxx
  \BODY
  haha
}

\begin{ack}
Middle body
\end{ack}
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)

    assert out[0] == EnvironmentStartToken("ack")
    assert out[-1] == Token(TokenType.ENVIRONMENT_END, "ack")

    body = out[1:-1]
    body_str = expander.convert_tokens_to_str(body).strip()
    assert body_str.startswith("XXX")
    assert "Middle body" in body_str
    assert body_str.endswith("haha")
