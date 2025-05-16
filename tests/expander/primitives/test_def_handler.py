import pytest

from latex2json.expander.expander_core import ExpanderCore
from latex2json.nodes import TextNode, ArgNode, BraceNode
from latex2json.expander.handlers.primitives.newdef import (
    get_def_usage_pattern_and_definition,
    get_parsed_args_from_usage_pattern,
    register_def,
)

from latex2json.nodes.syntactic_nodes import CommandNode
from tests.parser.test_parser_core import assert_ast_sequence


def test_get_def_usage_pattern_and_definition():
    expander = ExpanderCore()
    parser = expander.parser

    def test1():
        text = r"\def\test[#1:#2]{TEST #1:#2 ENDTEST}"
        expander.set_text(text)

        assert parser.parse_command() == CommandNode(r"\def")
        assert parser.parse_command() == CommandNode(r"\test")

        usage_pattern, definition = get_def_usage_pattern_and_definition(parser)
        assert usage_pattern is not None
        assert definition is not None

        expected_usage_pattern = [
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

        usage_pattern, definition = get_def_usage_pattern_and_definition(parser)
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

    test1()
    test2()


def test_parse_args_from_usage_pattern():
    expander = ExpanderCore()

    def test1():
        expander.set_text(r"[HELLO:{sdsd}]")
        usage_pattern = [
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

    test1()
    test2()


def test_def_handler():
    expander = ExpanderCore()

    register_def(expander)

    assert not expander.macros.get("test")
    expander.set_text(r"\def\test[#1:#2]{TEST #1:#2 ENDTEST}")
    expander.process()
    assert expander.macros.get("test")

    expander.set_text(r"\test[HELLO:world]")
    out = expander.process()
    assert out == [
        TextNode("TEST HELLO:world ENDTEST"),
    ]
