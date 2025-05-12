import pytest

from latex2json.nodes.syntactic_nodes import (
    TextNode,
    BraceNode,
    BracketNode,
    CommandNode,
    ArgNode,
    EndOfLineNode,
)


def test_text_node():
    text = TextNode("Hello")
    assert text.text == "Hello"
    assert str(text) == "'Hello'"

    # check equality
    assert text == TextNode("Hello")
    assert text != TextNode("World")
    assert text != BraceNode([])


def test_brace_node():
    brace = BraceNode([TextNode("Hello"), TextNode("World")])
    assert len(brace.children) == 2
    assert isinstance(brace.children[0], TextNode)
    assert isinstance(brace.children[1], TextNode)

    # check equality
    assert brace == BraceNode([TextNode("Hello"), TextNode("World")])
    assert brace != BraceNode([TextNode("Hello"), TextNode("Worlds")])
    assert brace != BracketNode([TextNode("Hello"), TextNode("World")])

    # check equality with nesting
    nested_brace = BraceNode([BraceNode([TextNode("Hello"), TextNode("World")])])
    assert nested_brace == BraceNode(
        [BraceNode([TextNode("Hello"), TextNode("World")])]
    )

    assert nested_brace != BraceNode(
        [BraceNode([TextNode("Hello"), TextNode("Worlds")])]
    )
    # not equal to bracket node
    assert nested_brace != BracketNode(
        [BraceNode([TextNode("Hello"), TextNode("World")])]
    )


def test_bracket_node():
    bracket = BracketNode([TextNode("Hello")])
    assert len(bracket.children) == 1
    assert isinstance(bracket.children[0], TextNode)

    # check equality
    assert bracket == BracketNode([TextNode("Hello")])
    assert bracket != BracketNode([TextNode("World")])
    assert bracket != BraceNode([TextNode("Hello")])


def test_command_node():
    # Test command with no arguments
    cmd = CommandNode("section")
    assert cmd.name == "section"
    assert len(cmd.args) == 0
    assert len(cmd.opt_args) == 0

    # Test command with arguments and optional arguments
    cmd_with_args = CommandNode(
        "section",
        args=[BraceNode([TextNode("Title")])],
        opt_args=[BracketNode([TextNode("opt")])],
    )
    assert cmd_with_args.name == "section"
    assert len(cmd_with_args.args) == 1
    assert len(cmd_with_args.opt_args) == 1

    # check equality
    assert cmd == CommandNode("section")
    assert cmd != CommandNode("subsection")
    assert cmd_with_args == CommandNode(
        "section",
        args=[BraceNode([TextNode("Title")])],
        opt_args=[BracketNode([TextNode("opt")])],
    )


def test_arg_node():
    arg = ArgNode(1, num_params=1)
    assert arg.num == 1
    assert arg.depth == 0
    assert arg.get_literal() == "#1"

    # Test with depth
    arg_depth = ArgNode(2, num_params=2)
    assert arg_depth.get_literal() == "##2"

    # check equality
    assert arg == ArgNode(1, num_params=1)
    assert arg != ArgNode(2, num_params=1)
    assert arg != ArgNode(1, num_params=2)


def test_end_of_line_node():
    eol = EndOfLineNode()

    # check equality
    assert eol == EndOfLineNode()
    assert eol != TextNode("\n")


def test_strip_whitespace():
    # Test stripping whitespace from BraceNode
    brace = BraceNode([TextNode("  Hello  "), TextNode("  World  ")])
    brace.strip_whitespace()
    assert brace.children[0].text == "Hello  "
    assert brace.children[1].text == "  World"
