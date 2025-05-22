import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token, TokenType
from tests.test_utils import assert_token_sequence


def test_basic_csname():
    expander = Expander()

    # Test basic csname creation
    out = expander.expand(r"\csname test\endcsname")
    assert_token_sequence(out, [Token(TokenType.CONTROL_SEQUENCE, "test")])


def test_nested_csname():
    expander = Expander()

    # Define some test macros
    expander.expand(r"\def\first{test}")
    expander.expand(r"\def\test{RESULT}")

    # Test nested csname using expansion
    out = expander.expand(r"\csname\first\endcsname")
    assert_token_sequence(out, expander.expand("RESULT"))


def test_multi_csname():
    expander = Expander()
    expander.expand(r"\def\foo{foo} \def\bar{BAR}")
    # note that just like in latex, inner \csname\bar\endcsname will fail
    out = expander.expand(r"\csname\foo\csname bar\endcsname\endcsname")
    assert_token_sequence(out, expander.expand(r"\fooBAR"))


def test_csname_with_spaces():
    expander = Expander()

    # Test that spaces are ignored in csname
    out = expander.expand(r"\csname test  token\endcsname")
    assert_token_sequence(out, [Token(TokenType.CONTROL_SEQUENCE, "testtoken")])


def test_csname_with_special_chars():
    expander = Expander()

    # Test csname with special characters
    out = expander.expand(r"\csname test123\endcsname")
    assert_token_sequence(out, [Token(TokenType.CONTROL_SEQUENCE, "test123")])


def test_csname_in_definition():
    expander = Expander()

    # Test using csname in macro definition
    expander.expand(r"\def\makemacro#1{\csname#1\endcsname}")
    expander.expand(r"\def\testmacro{SUCCESS}")

    out = expander.expand(r"\makemacro{testmacro}")
    assert_token_sequence(out, expander.expand("SUCCESS"))
