import pytest
from latex2json.nodes.definition_nodes import (
    NewCommandNode,
    NewEnvironmentNode,
    DefNode,
    LetNode,
)
from latex2json.nodes.syntactic_nodes import (
    TextNode,
    BraceNode,
    CommandNode,
    ArgNode,
)


def test_new_command_node():
    # Test basic command definition
    cmd = NewCommandNode(
        name="\\test",
        num_args=0,
        defaults=[],
        definition=[TextNode("Test content")],
    )
    assert cmd.name == "\\test"
    assert cmd.num_args == 0
    assert len(cmd.defaults) == 0
    assert isinstance(cmd.definition[0], TextNode)

    # Test with arguments and defaults
    cmd_with_args = NewCommandNode(
        name="\\complex",
        num_args=2,
        defaults=[[TextNode("default")]],
        definition=[ArgNode(1), TextNode(" and "), ArgNode(2)],
        depth=1,
    )
    assert cmd_with_args.num_args == 2
    assert len(cmd_with_args.defaults) == 1
    assert cmd_with_args.depth == 1

    # Test equality
    assert cmd == NewCommandNode(
        name="\\test",
        num_args=0,
        defaults=[],
        definition=[TextNode("Test content")],
    )
    assert cmd != NewCommandNode(
        name="\\test",
        num_args=0,
        defaults=[],
        definition=[TextNode("Different content")],
    )


def test_new_environment_node():
    # Test basic environment definition
    env = NewEnvironmentNode(
        name="custom",
        num_args=0,
        before_block=BraceNode([TextNode("Begin")]),
        after_block=BraceNode([TextNode("End")]),
        defaults=[],
    )
    assert env.name == "custom"
    assert env.num_args == 0
    assert len(env.defaults) == 0

    # Test equality
    assert env == NewEnvironmentNode(
        name="custom",
        num_args=0,
        before_block=BraceNode([TextNode("Begin")]),
        after_block=BraceNode([TextNode("End")]),
        defaults=[],
    )
    assert env != NewEnvironmentNode(
        name="different",
        num_args=0,
        before_block=BraceNode([TextNode("Begin")]),
        after_block=BraceNode([TextNode("End")]),
        defaults=[],
    )


def test_def_node():
    # Test basic def
    def_node = DefNode(
        name="\\test",
        usage_pattern=[ArgNode(1)],
        definition=[TextNode("content")],
    )
    assert def_node.name == "\\test"
    assert def_node.num_args == 1
    assert def_node.is_lazy is True
    assert def_node.is_global is False

    # Test global def
    gdef_node = DefNode(
        name="\\test",
        usage_pattern=[],
        definition=[TextNode("content")],
        is_global=True,
    )
    assert gdef_node.is_global is True

    # Test equality
    assert def_node == DefNode(
        name="\\test",
        usage_pattern=[ArgNode(1)],
        definition=[TextNode("content")],
    )
    assert def_node != DefNode(
        name="\\test",
        usage_pattern=[ArgNode(1)],
        definition=[TextNode("different")],
    )


def test_let_node():
    # Test basic let
    let_node = LetNode(
        name="\\newname",
        definition=CommandNode("oldname"),
    )
    assert let_node.name == "\\newname"
    assert let_node.is_future is False

    # Test future let
    future_let = LetNode(
        name="\\newname",
        definition=CommandNode("oldname"),
        is_future=True,
    )
    assert future_let.is_future is True

    # Test equality
    assert let_node == LetNode(
        name="\\newname",
        definition=CommandNode("oldname"),
    )
    assert let_node != LetNode(
        name="\\newname",
        definition=CommandNode("different"),
    )
