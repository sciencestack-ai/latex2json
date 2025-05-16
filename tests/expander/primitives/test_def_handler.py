import pytest

from latex2json.expander.expander_core import ExpanderCore
from latex2json.nodes import TextNode, ArgNode, BraceNode
from latex2json.expander.handlers.primitives.newdef import (
    get_def_usage_pattern_and_definition,
    get_parsed_args_from_usage_pattern,
    register_def,
)

from latex2json.nodes.syntactic_nodes import CommandNode, strip_whitespace
from tests.parser.test_parser_core import assert_ast_sequence


def test_get_def_usage_pattern_and_definition():
    expander = ExpanderCore()
    parser = expander.parser

    def test1():
        text = r"\def\test[[#1:#2]{TEST #1:#2 ENDTEST}"
        expander.set_text(text)

        assert parser.parse_command() == CommandNode(r"\def")
        assert parser.parse_command() == CommandNode(r"\test")

        usage_pattern, definition = get_def_usage_pattern_and_definition(expander)
        assert usage_pattern is not None
        assert definition is not None

        expected_usage_pattern = [
            TextNode("["),
            TextNode("["),
            ArgNode(1, 1),
            TextNode(":"),
            ArgNode(2, 1),
            TextNode("]"),
        ]
        assert_ast_sequence(usage_pattern, expected_usage_pattern)

        expected_definition = [
            TextNode("TEST"),
            TextNode(" "),
            ArgNode(1, 1),
            TextNode(":"),
            ArgNode(2, 1),
            TextNode(" "),
            TextNode("ENDTEST"),
        ]
        assert_ast_sequence(definition, expected_definition)

    def test2():
        text = r"\def\XXint##1##2##3{1) ##1 2) ##2 3) ##3 4)##4} % 4th arg is ignored"
        expander.set_text(text)

        assert parser.parse_command() == CommandNode(r"\def")
        assert parser.parse_command() == CommandNode(r"\XXint")

        usage_pattern, definition = get_def_usage_pattern_and_definition(expander)
        assert usage_pattern is not None
        assert definition is not None

        expected_usage_pattern = [
            ArgNode(1, 2),
            ArgNode(2, 2),
            ArgNode(3, 2),
        ]
        assert_ast_sequence(usage_pattern, expected_usage_pattern)

        expected_definition = [
            TextNode("1)"),
            TextNode(" "),
            ArgNode(1, 2),
            TextNode(" "),
            TextNode("2)"),
            TextNode(" "),
            ArgNode(2, 2),
            TextNode(" "),
            TextNode("3)"),
            TextNode(" "),
            ArgNode(3, 2),
            TextNode(" "),
            TextNode("4)"),
            ArgNode(4, 2),
        ]
        assert_ast_sequence(definition, expected_definition)

    def test3():
        text = r"\def\pair(#1, #2){1) #1 2) #2}"
        expander.set_text(text)

        assert parser.parse_command() == CommandNode(r"\def")
        assert parser.parse_command() == CommandNode(r"\pair")

        usage_pattern, definition = get_def_usage_pattern_and_definition(expander)
        assert usage_pattern is not None
        assert definition is not None

        expected_usage_pattern = [
            TextNode("("),
            ArgNode(1, 1),
            TextNode(","),
            TextNode(" "),
            ArgNode(2, 1),
            TextNode(")"),
        ]
        assert_ast_sequence(usage_pattern, expected_usage_pattern)

        expected_definition = [
            TextNode("1)"),
            TextNode(" "),
            ArgNode(1, 1),
            TextNode(" "),
            TextNode("2)"),
            TextNode(" "),
            ArgNode(2, 1),
        ]
        assert_ast_sequence(definition, expected_definition)

    test1()
    test2()
    test3()


def test_parse_args_from_usage_pattern():
    expander = ExpanderCore()

    def test1():
        expander.set_text(r"[[HELLO:{sdsd}]")
        usage_pattern = [
            TextNode("["),
            TextNode("["),
            ArgNode(1, 1),
            TextNode(":"),
            ArgNode(2, 1),
            TextNode("]"),
        ]
        out = get_parsed_args_from_usage_pattern(expander, usage_pattern)

        expected_parsed_args = [
            TextNode("HELLO"),
            BraceNode([TextNode("sdsd")]),
        ]
        assert_ast_sequence(out, expected_parsed_args)

    def test2():
        expander.set_text(r"{abc}a\cmd")
        usage_pattern = [
            ArgNode(1, 1),
            ArgNode(2, 1),
            ArgNode(3, 1),
        ]
        out = get_parsed_args_from_usage_pattern(expander, usage_pattern)

        expected_parsed_args = [
            BraceNode([TextNode("abc")]),
            TextNode("a"),
            CommandNode(r"\cmd"),
        ]
        assert_ast_sequence(out, expected_parsed_args)

        expander.set_text(r"a\cmd1ccc")
        out = get_parsed_args_from_usage_pattern(expander, usage_pattern)
        expected_parsed_args = [
            TextNode("a"),
            CommandNode(r"\cmd"),
            TextNode("1"),
        ]
        assert_ast_sequence(out, expected_parsed_args)

    def test3():
        expander.set_text(r"(aaa, {bbb})")
        usage_pattern = [
            TextNode("("),
            ArgNode(1, 1),
            TextNode(","),
            TextNode(" "),
            ArgNode(2, 1),
            TextNode(")"),
        ]
        out = get_parsed_args_from_usage_pattern(expander, usage_pattern)
        expected_parsed_args = [
            TextNode("aaa"),
            BraceNode([TextNode("bbb")]),
        ]
        assert_ast_sequence(out, expected_parsed_args)

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


def test_edef():
    expander = ExpanderCore()
    register_def(expander)

    # test instant expansion
    text = r"""
    \def\foo{FOO}
    \edef\bar#1{\foo #1}
    \def\foo{BAR} % shouldn't affect \bar since \edef\bar is already expanded
    \bar{3}
"""
    expander.set_text(text)
    out = expander.process()
    assert expander.macros.get("bar")
    assert expander.macros.get("foo")

    strip_whitespace(out)
    assert out == [
        TextNode("FOO 3"),
    ]

    # test edef inside scope
    text = r"""
    {
        \edef\bar{NEW BAR}
    }
    \bar{4} % STILL FOO due to scope
    """.strip()
    expander.set_text(text)
    out = expander.process()
    assert expander.macros.get("bar")
    assert expander.macros.get("foo")

    strip_whitespace(out)
    assert out == [
        TextNode("FOO 4"),
    ]
