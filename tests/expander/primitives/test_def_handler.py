import pytest

from latex2json.expander.expander_core import ExpanderCore
from latex2json.nodes import TextNode, ArgNode, BraceNode
from latex2json.expander.handlers.primitives.newdef import (
    get_def_usage_pattern_and_definition,
    get_parsed_args_from_usage_pattern,
    register_def,
)

from latex2json.nodes.syntactic_nodes import CommandNode, strip_whitespace
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from tests.test_utils import assert_ast_sequence, assert_token_sequence


def test_get_def_usage_pattern_and_definition():
    expander = ExpanderCore()
    parser = expander.parser

    def test1():
        text = r"\def\test[[#1:#2]{T #1:#2 ENDT}"
        expander.set_text(text)

        assert parser.parse_command() == CommandNode(r"\def")
        assert parser.parse_command() == CommandNode(r"\test")

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

        assert parser.parse_command() == CommandNode(r"\def")
        assert parser.parse_command() == CommandNode(r"\pair")

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
        expander.set_text(r"\def\test[#1:#2]{TEST #1:#2 ENDTEST}")
        expander.process()
        assert expander.macros.get("test")

        expander.set_text(r"\test[HELLO:world]")
        out = expander.process()
        assert out == [
            TextNode("TEST HELLO:world ENDTEST"),
        ]

    def test2():
        text = r"\def\foo(e#1{BAR #1 BAR} \def\hi{HI}"
        expander.set_text(text)
        expander.process()
        assert expander.macros.get("foo")
        assert expander.macros.get("hi")

        expander.set_text(r"\foo(e{33}")
        out = expander.process()
        assert out == [
            TextNode("BAR 33 BAR"),
        ]

        expander.set_text(r"\foo(ee")
        out = expander.process()
        assert out == [
            TextNode("BAR e BAR"),
        ]

        expander.set_text(r"\foo(e\hi")
        out = expander.process()
        assert out == [
            TextNode("BAR HI BAR"),
        ]

    test1()
    test2()


def test_def_redefine():
    expander = ExpanderCore()
    register_def(expander)

    text = r"""
    \def\foo{FOO}
    \def\bar{\foo}
    \def\foo{BAR}
    \bar
    """.strip()

    expander.set_text(text)
    out = expander.process()
    assert expander.macros.get("foo")
    assert expander.macros.get("bar")

    out = strip_whitespace(out)
    assert out == [
        TextNode("BAR"),
    ]


# def test_edef():
#     expander = ExpanderCore()
#     register_def(expander)

#     # test instant expansion
#     text = r"""
#     \def\foo{FOO}
#     \edef\bar#1{\foo #1}
#     \def\foo{BAR} % shouldn't affect \bar since \edef\bar is already expanded
#     \bar{3}
# """
#     expander.set_text(text)
#     out = expander.process()
#     assert expander.macros.get("bar")
#     assert expander.macros.get("foo")

#     strip_whitespace(out)
#     assert out == [
#         TextNode("FOO 3"),
#     ]

#     # test edef inside scope
#     text = r"""
#     {
#         \edef\bar{NEW BAR}
#         \edef\barry{BARRY}
#     }
#     \bar{4} % STILL FOO due to scope
#     """.strip()
#     expander.set_text(text)
#     out = expander.process()
#     assert expander.macros.get("bar")
#     assert expander.macros.get("foo")
#     assert not expander.macros.get("barry")  # out of scope

#     strip_whitespace(out)
#     assert out == [
#         TextNode("FOO 4"),
#     ]


# def test_gdef():
#     expander = ExpanderCore()
#     register_def(expander)

#     text = r"""
#     {
#         \def\foo{FOO}
#         \gdef\bar#1{\foo #1}
#     }
#     \foo\bar{3}
#     """.strip()
#     expander.set_text(text)
#     out = expander.process()
#     assert not expander.macros.get("foo")
#     assert expander.macros.get("bar")  # global \gdef

#     strip_whitespace(out)
#     assert out == [
#         CommandNode(r"\foo"),  # unresolved since \foo does not exist outside scope
#         CommandNode(r"\foo"),  # unresolved since \foo does not exist outside scope
#         TextNode(" 3"),
#     ]


# def test_xdef():
#     expander = ExpanderCore()
#     register_def(expander)

#     text = r"""
#     {
#         \def\foo{FOO}
#         \xdef\bar#1{\foo #1} % global
#         \def\foo{BAR}
#     }
#     \bar{3} % FOO 3 due to immediate expansion
#     """.strip()
#     expander.set_text(text)
#     out = expander.process()
#     assert not expander.macros.get("foo")
#     assert expander.macros.get("bar")  # global \xdef

#     strip_whitespace(out)
#     assert out == [
#         TextNode("FOO 3"),
#     ]


# def test_nested_defs():
#     expander = ExpanderCore()
#     register_def(expander)

#     text = r"""
#     \def\foo#1{
#         \def\bar##1{BAR #1 ##1}
#         \gdef\barx{\bar{BRO}}
#     }
#     \foo{hello}
#     \barx
#     """.strip()

#     expander.set_text(text)
#     out = expander.process()
#     assert expander.macros.get("foo")

#     strip_whitespace(out)
#     assert out == [
#         TextNode("BAR hello BRO"),
#     ]
