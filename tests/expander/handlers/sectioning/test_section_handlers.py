from typing import List, Optional
import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.types import (
    BEGIN_BRACE_TOKEN,
    END_BRACE_TOKEN,
    BEGIN_BRACKET_TOKEN,
    END_BRACKET_TOKEN,
    Token,
    TokenType,
)


def mock_section_token(
    expander: Expander,
    section_name: str,
    content: str,
    opt_arg: Optional[str] = None,
    numbering: Optional[str] = None,
):
    section_token = Token(TokenType.CONTROL_SEQUENCE, section_name)
    if numbering:
        section_token.numbering = numbering

    out_tokens = [section_token]
    if opt_arg:
        out_tokens.extend(
            [BEGIN_BRACKET_TOKEN] + expander.expand(opt_arg) + [END_BRACKET_TOKEN]
        )
    out_tokens.extend(
        [BEGIN_BRACE_TOKEN] + expander.expand(content) + [END_BRACE_TOKEN]
    )
    return out_tokens


def test_section_handler():
    expander = Expander()

    out = expander.expand(r"\section{Hello}")
    expected = mock_section_token(expander, "section", "Hello", numbering="1")
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

    # test with subsubsection with *
