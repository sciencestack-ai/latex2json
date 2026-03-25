import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from tests.test_utils import assert_token_sequence


def test_noexpand_basic():
    expander = Expander()

    # Test noexpand prevents macro expansion
    expander.expand(r"\def\foo{BAR}")

    # normally expands to BAR
    assert_token_sequence(expander.expand(r"\foo"), expander.expand("BAR"))

    # noexpand prevents expansion
    out = expander.expand(r"\noexpand\foo")
    assert_token_sequence(out, [Token(TokenType.CONTROL_SEQUENCE, "foo")])


def test_protect_basic():
    expander = Expander()

    expander.expand(r"\def\foo{BAR}")

    # \protect should keep the next token unexpanded (LaTeX moving-arg behavior)
    out = expander.expand(r"\protect\foo")
    assert_token_sequence(out, [Token(TokenType.CONTROL_SEQUENCE, "foo")])


def test_noexpand_with_csname():
    expander = Expander()

    out = expander.expand(r"\noexpand\csname1foo")
    expected = [Token(TokenType.CONTROL_SEQUENCE, "csname")] + expander.expand("1foo")
    assert_token_sequence(out, expected)


def test_noexpand_with_edef():
    expander = Expander()

    text = r"""
    \def\foo{FOO}
    \def\dnofoo{\noexpand\foo} % expands to \foo control sequence
    \edef\efoo{\foo} % expands to FOO
    \edef\enofoo{\noexpand\foo} % edef still expands to FOO, but the macro definition is \foo
    """
    expander.expand(text)
    assert_token_sequence(
        expander.expand(r"\dnofoo"), [Token(TokenType.CONTROL_SEQUENCE, "foo")]
    )
    assert_token_sequence(expander.expand(r"\enofoo"), expander.expand("FOO"))
    assert_token_sequence(expander.expand(r"\enofoo"), expander.expand(r"\efoo"))

    # but lets check how the edef macro itself stores the token definition
    efoo_macro = expander.get_macro(r"\efoo")
    enofoo_macro = expander.get_macro(r"\enofoo")
    assert efoo_macro is not None
    assert enofoo_macro is not None
    # efoo definition is FOO
    assert_token_sequence(efoo_macro.definition, expander.expand("FOO"))
    # enofoo definition is \foo
    assert_token_sequence(
        enofoo_macro.definition, [Token(TokenType.CONTROL_SEQUENCE, "foo")]
    )

    # test unexpanded with def
    text = r"""
    \def\bar{BAR}
    \edef\eunexpandednofoo{\unexpanded{\foo \bar}}
    """
    expander.expand(text)
    eunexpandednofoo_macro = expander.get_macro(r"\eunexpandednofoo")
    assert eunexpandednofoo_macro is not None
    assert_token_sequence(
        eunexpandednofoo_macro.definition,
        [
            Token(TokenType.CONTROL_SEQUENCE, "foo"),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.CONTROL_SEQUENCE, "bar"),
        ],
    )

    assert_token_sequence(
        expander.expand(r"\eunexpandednofoo"), expander.expand("FOO BAR")
    )


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
        expander.expand(r"\csname \foo bar\endcsname"),
        [Token(TokenType.CONTROL_SEQUENCE, "foobar")],
    )


def test_expandafter_edge_cases():
    expander = Expander()

    # Test expandafter at end of input
    out = expander.expand(r"\expandafter")
    assert_token_sequence(out, [])  # Should handle gracefully

    # Test expandafter with single token
    expander = Expander()
    text = r"""
    \def\expandafterbar{\expandafter\bar} % \expandafter doesnt strictly need 2 tokens
    \def\bar{BAR}
    """
    expander.expand(text)
    assert_token_sequence(expander.expand(r"\expandafterbar"), expander.expand("BAR"))


def test_ea_expands_content_inside():
    expander = Expander()
    text = r"""
    \def\ea#1{\expandafter#1}
    \ea{\def\csname afoo\endcsname{AFOO}}
    """
    expander.expand(text)
    out = expander.expand(r"\afoo")
    assert_token_sequence(out, expander.expand("AFOO"))

    # also works like
    text = r"""
    \ea{\def}\csname afoo\endcsname{AFOO2}
"""
    expander.expand(text)
    out = expander.expand(r"\afoo")
    assert_token_sequence(out, expander.expand("AFOO2"))

    text = r"""
\newcommand\eadef[1]{
    \expandafter\def\csname #1\endcsname##1:##2{RATIO ##1:##2}
}
\eadef{ratio}
""".strip()
    expander.expand(text)
    out = expander.expand(r"\ratio33:44")
    assert_token_sequence(out, expander.expand("RATIO 33:44"))


def test_unexpanded_basic():
    expander = Expander()

    # Test basic unexpanded functionality
    expander.expand(r"\def\foo{BAR}")

    # Without unexpanded, \foo expands to BAR
    assert_token_sequence(expander.expand(r"\foo"), expander.expand("BAR"))

    # With unexpanded, the tokens inside the braces remain unexpanded
    out = expander.expand(r"\unexpanded{\foo}")
    assert_token_sequence(out, [Token(TokenType.CONTROL_SEQUENCE, "foo")])

    # Test unexpanded with multiple tokens
    expander.expand(r"\def\bar{BAZ}")
    out = expander.expand(r"\unexpanded{\foo \bar}")
    assert_token_sequence(
        out,
        [
            Token(TokenType.CONTROL_SEQUENCE, "foo"),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.CONTROL_SEQUENCE, "bar"),
        ],
    )
