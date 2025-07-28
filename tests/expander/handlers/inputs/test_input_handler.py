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
test_data_path = os.path.join(dir_path, "../../../samples")


def test_input_handler():
    expander = Expander()

    # sample.tex contains a section
    text = r"""
    \def\myinput{\input{%s/example.tex}}
    
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

    # test that also works on .sty or .cls files
    assert not expander.get_macro("foo")
    expander.expand(r"\input{%s/package1.sty}" % test_data_path)
    assert expander.get_macro("foo")

    assert not expander.get_macro("somecmd")
    expander.expand(r"\input{%s/basecls.cls}" % test_data_path)
    assert expander.get_macro("somecmd")

    # check that anything post endinput is not reached
    text = r"""
    \input{%s/package2.sty}
    """ % (
        test_data_path
    )
    out = expander.expand(text)
    assert expander.get_macro("preendinput")
    assert not expander.get_macro("postendinput")
