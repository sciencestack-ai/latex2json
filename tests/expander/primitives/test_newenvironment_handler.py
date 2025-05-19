import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_basic_newenvironment():
    expander = Expander()

    # Basic command without arguments
    text = r"""
    \newenvironment*{hello} {HELLO} {BYE}
    """.strip()
    expander.expand(text)
    assert expander.macros.get("\\hello")
    assert expander.macros.get("\\endhello")

    out = expander.expand(r"\hello MIDDLE \endhello")
    assert_token_sequence(out, expander.expand("HELLO MIDDLE BYE"))

    # test only partial
    out = expander.expand(r"\hello")
    assert_token_sequence(out, expander.expand("HELLO"))

    out = expander.expand(r"\endhello")
    assert_token_sequence(out, expander.expand("BYE"))

    # requires begin_end to be registered
    out = expander.expand(r"\begin{hello} MIDDLE \end{hello}")
    assert_token_sequence(out, expander.expand("HELLO MIDDLE BYE"))


def test_environment_with_args():
    expander = Expander()

    text = r"""
    \newenvironment {hello}[2][default]{HELLO #1 THERE #2}{BYE}
    """.strip()
    expander.expand(text)

    out = expander.expand(r"\hello {BRO}MIDDLE\endhello")
    assert_token_sequence(out, expander.expand("HELLO default THERE BROMIDDLEBYE"))

    # check with malformed brace
    out = expander.expand(r"\hello [new]{BRO}{MIDDLE \endhello")
    assert_token_sequence(out, expander.expand("HELLO new THERE BRO{MIDDLE BYE"))

    # requires begin_end to be registered
    out = expander.expand(r"\begin{hello}[newdefault] {BROX} MIDDLE \end{hello}")
    assert_token_sequence(
        out, expander.expand("HELLO newdefault THERE BROX MIDDLE BYE")
    )


def test_nested_environments():
    expander = Expander()

    text = r"""
\newenvironment{test}[1]{
    \newenvironment{innertest}[1]{Begin #1 ##1}{END #1}
}{FINAL}
\test {333}\innertest{444}\endinnertest\endtest
    """
    out = expander.expand(text)
    strip_whitespace_tokens(out)

    assert_token_sequence(out, expander.expand("Begin 333 444END 333FINAL"))
