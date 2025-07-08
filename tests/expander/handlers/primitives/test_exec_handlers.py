import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_exec_handlers():
    expander = Expander()

    text = r"""
    \makeatletter
    \newwrite\filexx
    \openout\@auxout = test.aux
    \immediate\write\@auxout{test}
    \write\filexx{aaa}
    \closeout\@auxout
    """

    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out == []
