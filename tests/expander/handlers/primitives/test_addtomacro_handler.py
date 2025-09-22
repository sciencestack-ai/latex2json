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


def test_addtomacro_handler():
    expander = Expander()

    # if not defined, just define it
    text = r"""
    \makeatletter
    \g@addto@macro{\foo}{bar}
    \foo % \foo was not defined, but now it is
"""
    expander.expand(text)
    assert expander.get_macro("foo")
    assert_token_sequence(expander.expand(r"\foo"), expander.expand("bar"))

    # now add to it
    text = r"""\g@addto@macro{\foo}{baz}"""
    expander.expand(text)
    assert_token_sequence(expander.expand(r"\foo"), expander.expand("barbaz"))
