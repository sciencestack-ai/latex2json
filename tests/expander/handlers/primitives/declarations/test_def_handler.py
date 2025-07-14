import pytest

from latex2json.expander.expander_core import RELAX_TOKEN
from latex2json.expander.expander import Expander
from latex2json.expander.handlers.primitives.declarations.def_handler import (
    get_def_usage_pattern_and_definition,
    get_parsed_args_from_usage_pattern,
)

from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token, TokenType
from tests.test_utils import assert_token_sequence


def test_get_def_usage_pattern_and_definition():
    expander = Expander()

    def test1():
        text = r"\def\test[[#1:#2]{T #1:#2 ENDT}"
        expander.set_text(text)

        assert expander.consume() == Token(TokenType.CONTROL_SEQUENCE, "def")
        assert expander.consume() == Token(TokenType.CONTROL_SEQUENCE, "test")

        usage_pattern, definition = get_def_usage_pattern_and_definition(expander)
        assert usage_pattern is not None
        assert definition is not None

        expected_usage_pattern = [
            Token(TokenType.CHARACTER, "[", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "[", catcode=Catcode.OTHER),
            Token(TokenType.PARAMETER, "1"),
            Token(TokenType.CHARACTER, ":", catcode=Catcode.OTHER),
            Token(TokenType.PARAMETER, "2"),
            Token(TokenType.CHARACTER, "]", catcode=Catcode.OTHER),
        ]
        assert_token_sequence(usage_pattern, expected_usage_pattern)

        expected_definition = [
            Token(TokenType.CHARACTER, "T", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.PARAMETER, "1"),
            Token(TokenType.CHARACTER, ":", catcode=Catcode.OTHER),
            Token(TokenType.PARAMETER, "2"),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.CHARACTER, "E", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "N", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "D", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "T", catcode=Catcode.LETTER),
        ]
        assert_token_sequence(definition, expected_definition)

    def test2():
        text = r"\def\pair(#1, #2){1) #1 2) #2}"
        expander.set_text(text)

        assert expander.consume() == Token(TokenType.CONTROL_SEQUENCE, "def")
        assert expander.consume() == Token(TokenType.CONTROL_SEQUENCE, "pair")

        usage_pattern, definition = get_def_usage_pattern_and_definition(expander)
        assert usage_pattern is not None
        assert definition is not None

        expected_usage_pattern = [
            Token(TokenType.CHARACTER, "(", catcode=Catcode.OTHER),
            Token(TokenType.PARAMETER, "1"),
            Token(TokenType.CHARACTER, ",", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.PARAMETER, "2"),
            Token(TokenType.CHARACTER, ")", catcode=Catcode.OTHER),
        ]
        assert_token_sequence(usage_pattern, expected_usage_pattern)

        expected_definition = [
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, ")", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.PARAMETER, "1"),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, ")", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.PARAMETER, "2"),
        ]
        assert_token_sequence(definition, expected_definition)

    test1()
    test2()


def test_parse_args_from_usage_pattern():
    expander = Expander()

    def test_with_brackets():
        # usage: [[#1:#2]
        expander.set_text(r"[[HI:{123}\cmd]")
        usage_pattern = [
            Token(TokenType.CHARACTER, "[", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "[", catcode=Catcode.OTHER),
            Token(TokenType.PARAMETER, "1"),
            Token(TokenType.CHARACTER, ":", catcode=Catcode.OTHER),
            Token(TokenType.PARAMETER, "2"),
            Token(TokenType.CHARACTER, "]", catcode=Catcode.OTHER),
        ]
        out = get_parsed_args_from_usage_pattern(expander, usage_pattern)

        arg1 = [
            Token(TokenType.CHARACTER, "H", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "I", catcode=Catcode.LETTER),
        ]
        arg2 = [
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "3", catcode=Catcode.OTHER),
            Token(TokenType.CONTROL_SEQUENCE, "cmd"),
        ]
        expected_parsed_args = [
            arg1,
            arg2,
        ]
        assert_token_sequence(out, expected_parsed_args)

    def test_regular():
        # usage: #1#2#3
        expander.set_text(r"{abc}a\cmd")
        usage_pattern = [
            Token(TokenType.PARAMETER, "1"),
            Token(TokenType.PARAMETER, "2"),
            Token(TokenType.PARAMETER, "3"),
        ]
        out = get_parsed_args_from_usage_pattern(expander, usage_pattern)

        arg1 = [
            Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "b", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "c", catcode=Catcode.LETTER),
        ]
        arg2 = [
            Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
        ]
        arg3 = [
            Token(TokenType.CONTROL_SEQUENCE, "cmd"),
        ]
        expected_parsed_args = [
            arg1,
            arg2,
            arg3,
        ]
        assert_token_sequence(out, expected_parsed_args)

    def test_with_braces():
        # usage: (#1, #2)
        expander.set_text(r"(aaa, {bbb}a)")
        usage_pattern = [
            Token(TokenType.CHARACTER, "(", catcode=Catcode.OTHER),
            Token(TokenType.PARAMETER, "1"),
            Token(TokenType.CHARACTER, ",", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
            Token(TokenType.PARAMETER, "2"),
            Token(TokenType.CHARACTER, ")", catcode=Catcode.OTHER),
        ]
        out = get_parsed_args_from_usage_pattern(expander, usage_pattern)

        arg1 = [
            Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
        ]
        arg2 = [
            Token(TokenType.CHARACTER, "b", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "b", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "b", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
        ]
        expected_parsed_args = [
            arg1,
            arg2,
        ]
        assert_token_sequence(out, expected_parsed_args)

    def test_with_control_sequence():
        # test with control sequence between arguments
        expander.set_text(r"a\xxx{123}")
        usage_pattern = [
            Token(TokenType.PARAMETER, "1"),
            Token(
                TokenType.PARAMETER, "2"
            ),  # note empty! since \xxx is a control sequence identical to \xxx in usage pattern
            Token(TokenType.CONTROL_SEQUENCE, "xxx"),
            Token(TokenType.PARAMETER, "3"),
        ]
        out = get_parsed_args_from_usage_pattern(expander, usage_pattern)
        arg1 = [
            Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
        ]
        arg2 = []  # note empty!
        arg3 = [
            Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "3", catcode=Catcode.OTHER),
        ]
        expected_parsed_args = [arg1, arg2, arg3]
        assert_token_sequence(out, expected_parsed_args)

    def test_prioritize_keyword_sequence():
        # test prioritizing keyword sequence over parameter
        # mock
        # \def\yyy#1haha#2{MUHAHA #1, #2 AHAHAH}
        # \yyy hah haha eee % note that the parser should exact match the 'haha' in the middle, and not the first 'hah'
        # thus, #1 -> 'hah ', #2 -> e

        expander.set_text(r"hah haha eee")

        usage_pattern = [
            Token(TokenType.PARAMETER, "1"),
            Token(TokenType.CHARACTER, "h", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
            Token(TokenType.CHARACTER, "ha", catcode=Catcode.LETTER),
            Token(TokenType.PARAMETER, "2"),
        ]
        out = get_parsed_args_from_usage_pattern(expander, usage_pattern)

        arg1 = expander.convert_str_to_tokens("hah ")
        arg2 = expander.convert_str_to_tokens("e")
        expected_parsed_args = [arg1, arg2]
        assert_token_sequence(out, expected_parsed_args)

    test_with_brackets()
    test_regular()
    test_with_braces()
    test_with_control_sequence()
    test_prioritize_keyword_sequence()


def test_def_handler():
    expander = Expander()

    def test1():
        assert not expander.get_macro("test")
        expander.expand(r"\long\def \test[#1:#2]{TEST #1:#2 ENDTEST}")
        assert expander.get_macro("test")

        out = expander.expand(r"\test[HELLO:world]")
        expected = expander.expand("TEST HELLO:world ENDTEST")
        assert_token_sequence(out, expected)

        assert expander.check_macro_is_user_defined("test")

    def test2():
        text = r"\def\foo(e#1{BAR #1 BAR} \def\hi{HI}"
        expander.expand(text)
        assert expander.get_macro("foo")
        assert expander.get_macro("hi")

        out = expander.expand(r"\foo(e{33}")
        expected = expander.expand("BAR 33 BAR")
        assert_token_sequence(out, expected)

        out = expander.expand(r"\foo(ee")
        expected = expander.expand("BAR e BAR")
        assert_token_sequence(out, expected)

        out = expander.expand(r"\foo(e\hi")
        expected = expander.expand("BAR HI BAR")
        assert_token_sequence(out, expected)

    def test3():
        text = r"\def\shout!#1!{shout #1}"
        expander.expand(text)
        assert expander.get_macro("shout")

        out = expander.expand(r"\shout!hello!")
        expected = expander.expand("shout hello")
        assert_token_sequence(out, expected)

    def test4():
        text = r"\def\swap#1#2{S#2#1S}"
        expander.expand(text)
        assert expander.get_macro("swap")

        out = expander.expand(r"\swap{hello}{world}")
        expected = expander.expand("SworldhelloS")
        assert_token_sequence(out, expected)
        out = expander.expand(r"\swap a b")
        expected = expander.expand("SbaS")
        assert_token_sequence(out, expected)

    def test5():
        # test with control sequence between arguments
        text = r"""\def\xxx#1#2\xxx#3{1) #1, 2) #2, 3) #3}"""
        expander.expand(text)
        assert expander.get_macro("xxx")
        out = expander.expand(r"\xxx a\xxx{TRES}")
        expected = expander.expand("1) a, 2) , 3) TRES")
        assert_token_sequence(out, expected)

        out = expander.expand(r"\xxx ab\xxx3")
        expected = expander.expand("1) a, 2) b, 3) 3")
        assert_token_sequence(out, expected)

    test1()
    test2()
    test3()
    test4()
    test5()


def test_def_redefine():
    expander = Expander()

    text = r"""
    \def\foo{FOO}
    \long\def\bar{\foo}
    \def\foo{BAR}
    """.strip()

    expander.expand(text)
    assert expander.get_macro("foo")
    assert expander.get_macro("bar")

    assert_token_sequence(expander.expand(r"\bar"), expander.expand("BAR"))


def test_def_with_global():
    expander = Expander()

    # not exist due to scope
    text = r"""{ \def\foo{FOO} }"""

    expander.expand(text)
    assert not expander.get_macro("foo")
    assert_token_sequence(
        expander.expand(r"\foo"), [Token(TokenType.CONTROL_SEQUENCE, "foo")]
    )

    # now test with global
    text = r"""{ \global\def\foo {FOO} }"""
    expander.expand(text)
    assert expander.get_macro("foo")
    assert_token_sequence(expander.expand(r"\foo"), expander.expand("FOO"))

    # ensure \global is not persisting...
    text = r"""{ \def\bar{BAR} }"""
    expander.expand(text)
    assert not expander.get_macro("bar")


def test_nested_defs2():
    expander = Expander()

    text = r"""
    \def\foo#1 {
        \def\bar##1{BAR #1 ##1}
        \def\barx{\bar{BRO}}
    }
    \foo{hello}
    """.strip()

    expander.expand(text)
    assert expander.get_macro("foo")
    assert expander.get_macro("bar")
    assert expander.get_macro("barx")

    assert_token_sequence(expander.expand(r"\barx"), expander.expand("BAR hello BRO"))


def test_gdef():
    expander = Expander()

    text = r"""
    {
        \def\foo{FOO}
        \gdef\bar#1{\foo #1}
    }
    """.strip()

    expander.expand(text)
    assert not expander.get_macro("foo")
    assert expander.get_macro("bar")  # global \gdef

    # unresolved since \foo does not exist outside scope
    assert_token_sequence(
        expander.expand(r"\foo\bar{3}"), expander.expand(r"\foo\foo 3")
    )

    # now define \foo
    expander.expand(r"\def\foo{FOO}")
    assert expander.get_macro("foo")
    assert_token_sequence(expander.expand(r"\bar{3}"), expander.expand("FOO 3"))


def test_edef():
    expander = Expander()

    # test instant expansion
    text = r"""
    \def\foo{FOO}
    \edef\bar#1{\foo #1} % immediate expansion to FOO #1
    \def\foo{BAR} % shouldn't affect \bar since \edef\bar is already expanded
    \bar{3}
"""
    expander.expand(text)
    assert expander.get_macro("bar")
    assert expander.get_macro("foo")

    assert_token_sequence(expander.expand(r"\bar{3}"), expander.expand("FOO 3"))

    # test edef inside scope
    text = r"""
    {
        \edef\bar{NEW BAR}
        \edef\barry{BARRY}
    }
    \bar{4} % STILL FOO due to scope (from above)
    """.strip()
    expander.expand(text)
    assert expander.get_macro("bar")
    assert not expander.get_macro("barry")  # out of scope

    assert_token_sequence(expander.expand(r"\bar{4}"), expander.expand("FOO 4"))

    # test edef with \relax (preserve \relax token)
    text = r"""
    \def\foo{FOO\relax}
    \edef\bar{\relax\foo\empty}
    """.strip()
    expander.expand(text)
    expected = [
        RELAX_TOKEN,
        *expander.expand("FOO"),
        RELAX_TOKEN,
    ]
    assert_token_sequence(expander.expand(r"\bar"), expected)


def test_xdef():
    expander = Expander()

    text = r"""
    {
        \def\foo{FOO}
        \xdef\bar#1{\foo #1} % global
        \long\def\foo{BAR}
    }
    \bar{3} % FOO 3 due to immediate expansion
    """.strip()

    expander.expand(text)
    assert not expander.get_macro("foo")
    assert expander.get_macro("bar")  # global \xdef

    assert_token_sequence(expander.expand(r"\bar{3}"), expander.expand("FOO 3"))


def test_nested_defs():
    expander = Expander()

    text = r"""
    \def\foo#1{
        {
            \def\bar##1{BAR #1 ##1}
            \gdef\barx{\bar{BRO}}
        }
    }
    \foo{hello}
    \barx
    """.strip()

    expander.expand(text)
    assert expander.get_macro("foo")
    assert expander.get_macro("barx")
    assert not expander.get_macro("bar")

    # Since \bar is not defined in scope, \barx expands literally
    expected = [
        Token(TokenType.CONTROL_SEQUENCE, "bar"),
        BEGIN_BRACE_TOKEN,
        Token(TokenType.CHARACTER, "B", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, "R", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, "O", catcode=Catcode.LETTER),
        END_BRACE_TOKEN,
    ]
    assert_token_sequence(expander.expand(r"\barx"), expected)

    # Now define \bar in scope
    expander.expand(r"\def\bar{BAR}")
    assert expander.get_macro("bar")
    assert_token_sequence(expander.expand(r"\barx"), expander.expand("BAR{BRO}"))


def test_more_defs():
    expander = Expander()

    text = r"""
    \def\numberone{ONE}
    \def \numbertwo{TWO}
    \def\XXint#1#2#3{1) #1 2) #2 3) #3 4)#4} % 4th arg is ignored
    \def\Xint#1{\XXint\numberone\numbertwo{#1}}
    \Xint{THREE}
    """.strip()

    expander.expand(text)
    assert expander.get_macro("XXint")
    assert expander.get_macro("Xint")

    assert_token_sequence(
        expander.expand(r"\Xint{THREE}"), expander.expand("1) ONE 2) TWO 3) THREE 4)")
    )


def test_def_nesting_doesnot_affect_control_sequence():
    expander = Expander()

    text = r"""
    \def\abs#1{AB #1 S}
    \def\ab#1{\abs#1} 
    \ab{xbc} % -> \absxbc, where \abs is already a control sequence so it will be equivalent to \abs{x}bc
    """

    expander.expand(text)
    assert expander.get_macro("abs")
    assert expander.get_macro("ab")

    assert_token_sequence(expander.expand(r"\ab{xbc}"), expander.expand("AB x Sbc"))


def test_weird_nested_noexpand_case():
    expander = Expander()

    text = r"""
    \makeatletter

    \newcommand\def@ult[1]{
        \edef\temp@a{\lowercase{\edef\noexpand\temp@a{#1}}}\temp@a
    }

    \def@ult{ABCDEF} % basically defines \temp@a as abcdef
    \temp@a % -> abcdef
    """

    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "abcdef"
