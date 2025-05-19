import pytest

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.primitives.newdef import (
    get_def_usage_pattern_and_definition,
    get_parsed_args_from_usage_pattern,
    register_def,
)

from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN, Token, TokenType
from tests.test_utils import assert_token_sequence


def test_get_def_usage_pattern_and_definition():
    expander = ExpanderCore()

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
    expander = ExpanderCore()

    def test1():
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

    def test2():
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

    def test3():
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

    test1()
    test2()
    test3()


def test_def_handler():
    expander = ExpanderCore()

    register_def(expander)

    def test1():
        assert not expander.macros.get("test")
        expander.expand(r"\def\test[#1:#2]{TEST #1:#2 ENDTEST}")
        assert expander.macros.get("test")

        out = expander.expand(r"\test[HELLO:world]")
        expected = expander.expand("TEST HELLO:world ENDTEST")
        assert_token_sequence(out, expected)

    def test2():
        text = r"\def\foo(e#1{BAR #1 BAR} \def\hi{HI}"
        expander.expand(text)
        assert expander.macros.get("foo")
        assert expander.macros.get("hi")

        out = expander.expand(r"\foo(e{33}")
        expected = expander.expand("BAR 33 BAR")
        assert_token_sequence(out, expected)

        out = expander.expand(r"\foo(ee")
        expected = expander.expand("BAR e BAR")
        assert_token_sequence(out, expected)

        out = expander.expand(r"\foo(e\hi")
        expected = expander.expand("BAR HI BAR")
        assert_token_sequence(out, expected)

    test1()
    test2()


def test_def_redefine():
    expander = ExpanderCore()
    register_def(expander)

    text = r"""
    \def\foo{FOO}
    \def\bar{\foo}
    \def\foo{BAR}
    """.strip()

    expander.expand(text)
    assert expander.macros.get("foo")
    assert expander.macros.get("bar")

    assert_token_sequence(expander.expand(r"\bar"), expander.expand("BAR"))


def test_nested_defs():
    expander = ExpanderCore()
    register_def(expander)

    text = r"""
    \def\foo#1{
        \def\bar##1{BAR #1 ##1}
        \def\barx{\bar{BRO}}
    }
    \foo{hello}
    """.strip()

    expander.expand(text)
    assert expander.macros.get("foo")
    assert expander.macros.get("bar")
    assert expander.macros.get("barx")

    assert_token_sequence(expander.expand(r"\barx"), expander.expand("BAR hello BRO"))


def test_gdef():
    expander = ExpanderCore()
    register_def(expander)

    text = r"""
    {
        \def\foo{FOO}
        \gdef\bar#1{\foo #1}
    }
    """.strip()

    expander.expand(text)
    assert not expander.macros.get("foo")
    assert expander.macros.get("bar")  # global \gdef

    # unresolved since \foo does not exist outside scope
    assert_token_sequence(
        expander.expand(r"\foo\bar{3}"), expander.expand(r"\foo\foo 3")
    )

    # now define \foo
    expander.expand(r"\def\foo{FOO}")
    assert expander.macros.get("foo")
    assert_token_sequence(expander.expand(r"\bar{3}"), expander.expand("FOO 3"))


def test_edef():
    expander = ExpanderCore()
    register_def(expander)

    # test instant expansion
    text = r"""
    \def\foo{FOO}
    \edef\bar#1{\foo #1} % immediate expansion to FOO #1
    \def\foo{BAR} % shouldn't affect \bar since \edef\bar is already expanded
    \bar{3}
"""
    expander.expand(text)
    assert expander.macros.get("bar")
    assert expander.macros.get("foo")

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
    assert expander.macros.get("bar")
    assert expander.macros.get("foo")
    assert not expander.macros.get("barry")  # out of scope

    assert_token_sequence(expander.expand(r"\bar{4}"), expander.expand("FOO 4"))


def test_xdef():
    expander = ExpanderCore()
    register_def(expander)

    text = r"""
    {
        \def\foo{FOO}
        \xdef\bar#1{\foo #1} % global
        \def\foo{BAR}
    }
    \bar{3} % FOO 3 due to immediate expansion
    """.strip()

    expander.expand(text)
    assert not expander.macros.get("foo")
    assert expander.macros.get("bar")  # global \xdef

    assert_token_sequence(expander.expand(r"\bar{3}"), expander.expand("FOO 3"))


def test_nested_defs():
    expander = ExpanderCore()
    register_def(expander)

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
    assert expander.macros.get("foo")
    assert expander.macros.get("barx")
    assert not expander.macros.get("bar")

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
    assert expander.macros.get("bar")
    assert_token_sequence(expander.expand(r"\barx"), expander.expand("BAR{BRO}"))
