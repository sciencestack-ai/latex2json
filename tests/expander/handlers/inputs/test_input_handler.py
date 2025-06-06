import pytest, os

from latex2json.expander.expander import Expander
from latex2json.tokens.types import TokenType
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import (
    assert_token_sequence,
    assert_tokens_startwith,
    assert_tokens_endwith,
)


dir_path = os.path.dirname(os.path.abspath(__file__))
test_data_path = os.path.join(dir_path, "../../test_data")


def test_input_handler():
    expander = Expander()

    # sample.tex contains a section
    text = r"""
    \def\myinput{\input{%s/sample.tex}}
    
    For some \myinput

    POST 
""" % (
        test_data_path
    )
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert_tokens_startwith(out, expander.expand("For some "))
    assert_tokens_endwith(out, expander.expand(" POST"))

    has_section = False
    for token in out:
        if token.type == TokenType.COMMAND_WITH_ARGS and token.value == "section":
            has_section = True
            break

    assert has_section
