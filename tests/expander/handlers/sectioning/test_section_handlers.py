from typing import List, Optional
import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.types import (
    CommandWithArgsToken,
    Token,
    TokenType,
)


def mock_section_token(
    expander: Expander,
    section_name: str,
    content: str,
    opt_arg: Optional[str] = None,
    numbering: Optional[str] = None,
    counter_name: Optional[str] = None,
):

    content_tokens = expander.convert_str_to_tokens(content)
    opt_arg_tokens = expander.convert_str_to_tokens(opt_arg) if opt_arg else []
    section_token = CommandWithArgsToken(
        name=section_name,
        args=[content_tokens],
        opt_args=[opt_arg_tokens] if opt_arg_tokens else [],
        numbering=numbering,
        counter_name=counter_name,
    )

    return [section_token]


def test_section_handler():
    expander = Expander()

    expander.expand(r"\def\titlex{TITLE}")

    out = expander.expand(r"\section{\titlex}")
    expected = mock_section_token(expander, "section", "TITLE", numbering="1")
    assert expander.check_tokens_equal(out, expected)

    # test with *
    out = expander.expand(r"\section* [OPT] {Hello}")
    expected = mock_section_token(expander, "section", "Hello", opt_arg="OPT")
    assert expander.check_tokens_equal(out, expected)

    out = expander.expand(r"\section [Hello]{Hello}")
    expected = mock_section_token(
        expander, "section", "Hello", opt_arg="Hello", numbering="2"
    )
    assert expander.check_tokens_equal(out, expected)

    # now test with subsection
    out = expander.expand(r"\subsection {Hello}")
    expected = mock_section_token(expander, "subsection", "Hello", numbering="2.1")
    assert expander.check_tokens_equal(out, expected)

    # test with subsubsection
    out = expander.expand(r"\subsubsection* {Hello}")
    expected = mock_section_token(expander, "subsubsection", "Hello")
    assert expander.check_tokens_equal(out, expected)

    out = expander.expand(r"\subsubsection {Hello}")
    expected = mock_section_token(expander, "subsubsection", "Hello", numbering="2.1.1")
    assert expander.check_tokens_equal(out, expected)

    # test with paragraph
    out = expander.expand(r"\paragraph {Hello}")
    expected = mock_section_token(expander, "paragraph", "Hello", numbering="2.1.1.1")
    assert expander.check_tokens_equal(out, expected)

    # test appendix numbering
    expander.expand(r"\appendix")
    out = expander.expand(r"\section {Hello}")
    expected = mock_section_token(expander, "section", "Hello", numbering="A")
    assert expander.check_tokens_equal(out, expected)

    out = expander.expand(r"\subsection{Hello}")
    expected = mock_section_token(expander, "subsection", "Hello", numbering="A.1")
    assert expander.check_tokens_equal(out, expected)

    # increment section counter
    out = expander.expand(r"\section{Hello}")
    expected = mock_section_token(expander, "section", "Hello", numbering="B")
    assert expander.check_tokens_equal(out, expected)
