import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token, TokenType
from tests.test_utils import assert_token_sequence


def test_noexpand_basic():
    expander = Expander()

    # Test noexpand prevents macro expansion
    expander.expand(r"\def\foo{BAR}")
    out = expander.expand(r"\noexpand\foo")
    assert_token_sequence(out, [Token(TokenType.CONTROL_SEQUENCE, "foo")])


def test_noexpand_with_csname():
    expander = Expander()

    # # Test noexpand with csname
    # expander.expand(r"\def\test{RESULT}")
    # out = expander.expand(r"\noexpand\csname test\endcsname")
    # assert_token_sequence(out, [Token(TokenType.CONTROL_SEQUENCE, "csname")])

    # # Test that csname still works after noexpand is done
    # out = expander.expand(r"\expandafter\noexpand\csname test\endcsname")
    # assert_token_sequence(out, [Token(TokenType.CONTROL_SEQUENCE, "test")])


def test_expandafter_with_csname_and_def():
    expander = Expander()

    # Test expandafter with csname
    expander.expand(r"\def\foo{test}")
    expander.expand(r"\def\test{RESULT}")

    # Without expandafter, \csname\foo\endcsname expands to \test which then expands to RESULT
    out = expander.expand(r"\csname\foo\endcsname")
    assert_token_sequence(out, expander.expand("RESULT"))

    # in \def, \csname\foo\endcsname expands to \test, which \def then redefines to TEST
    expander.expand(r"\expandafter\def\csname\foo\endcsname{TEST}")
    assert_token_sequence(expander.expand(r"\test"), expander.expand("TEST"))

    # test with nested \def \csnames
    text = r"""
    \def\foo{foo}
    \def\bar{BAR}
    \expandafter\def\csname\foo\csname bar\endcsname\endcsname{FUUBAR}
"""
    expander.expand(text)
    assert_token_sequence(expander.expand(r"\fooBAR"), expander.expand("FUUBAR"))
    assert_token_sequence(
        expander.expand(r"\csname fooBAR\endcsname"), expander.expand("FUUBAR")
    )
    assert_token_sequence(
        expander.expand(r"\csname \foo\bar\endcsname"), expander.expand("FUUBAR")
    )
    assert_token_sequence(
        expander.expand(r"\csname \foo bar\endcsname"), expander.expand(r"\foobar")
    )


def test_expandafter_edge_cases():
    expander = Expander()

    # Test expandafter at end of input
    out = expander.expand(r"\expandafter")
    assert_token_sequence(out, [])  # Should handle gracefully

    # # Test expandafter with single token
    # expander.expand(r"\def\foo{BAR}")
    # out = expander.expand(r"\expandafter\foo")
    # assert_token_sequence(out, expander.expand("BAR"))  # Should handle gracefully
