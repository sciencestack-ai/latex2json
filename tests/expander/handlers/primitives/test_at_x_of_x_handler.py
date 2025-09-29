import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import (
    EnvironmentEndToken,
    EnvironmentStartToken,
    Token,
    TokenType,
)
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.expander.handlers.sectioning.test_section_handlers import mock_section_token
from tests.test_utils import assert_token_sequence


def test_at_x_of_x_handler():
    expander = Expander()

    # if not defined, just define it
    text = r"""
\makeatletter
    
\@firstoftwo{ONE}{TWO}
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "ONE"

    assert expander.expand(r"\@secondoftwo{ONE}{TWO}") == expander.expand("TWO")
