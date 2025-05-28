import pytest

from latex2json.nodes import (
    TextNode,
    CommandNode,
)


def test_text_node():
    text = TextNode("Hello")
    assert text.text == "Hello"
    assert str(text) == "'Hello'"

    # check equality
    assert text == TextNode("Hello")
    assert text != TextNode("World")


def test_command_node():
    # Test command with no arguments
    cmd = CommandNode("section")
    assert cmd.name == "section"
    assert len(cmd.args) == 0
    assert len(cmd.opt_args) == 0

    # Test command with arguments and optional arguments
    cmd_with_args = CommandNode(
        "section",
        args=[[TextNode("Title")]],
        opt_args=[[TextNode("opt")]],
    )
    assert cmd_with_args.name == "section"
    assert len(cmd_with_args.args) == 1
    assert len(cmd_with_args.opt_args) == 1

    # check equality
    assert cmd == CommandNode("section")
    assert cmd != CommandNode("subsection")
    assert cmd_with_args == CommandNode(
        "section",
        args=[[TextNode("Title")]],
        opt_args=[[TextNode("opt")]],
    )
