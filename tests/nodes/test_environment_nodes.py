import pytest
from latex2json.nodes.environment_nodes import EnvironmentNode
from latex2json.nodes.syntactic_nodes import TextNode, BraceNode, BracketNode


def test_environment_node():
    # Test basic environment with no arguments
    env = EnvironmentNode(
        name="document",
        opt_args=[],
        args=[],
        body=[TextNode("Hello World")],
    )
    assert env.name == "document"
    assert len(env.opt_args) == 0
    assert len(env.args) == 0
    assert len(env.body) == 1
    assert isinstance(env.body[0], TextNode)

    # Test environment with optional arguments and arguments
    env_with_args = EnvironmentNode(
        name="figure",
        opt_args=[BracketNode([TextNode("htb")])],
        args=[BraceNode([TextNode("0.8\\textwidth")])],
        body=[TextNode("Figure content")],
    )
    assert env_with_args.name == "figure"
    assert len(env_with_args.opt_args) == 1
    assert len(env_with_args.args) == 1
    assert len(env_with_args.body) == 1

    # Test equality
    assert env == EnvironmentNode(
        name="document",
        opt_args=[],
        args=[],
        body=[TextNode("Hello World")],
    )
    assert env != EnvironmentNode(
        name="document",
        opt_args=[],
        args=[],
        body=[TextNode("Different content")],
    )
    assert env != EnvironmentNode(
        name="different",
        opt_args=[],
        args=[],
        body=[TextNode("Hello World")],
    )
    assert env != EnvironmentNode(
        name="document",
        opt_args=[TextNode("opt")],
        args=[],
        body=[TextNode("Hello World")],
    )

    # test equality with args
    assert env_with_args == EnvironmentNode(
        name="figure",
        opt_args=[BracketNode([TextNode("htb")])],
        args=[BraceNode([TextNode("0.8\\textwidth")])],
        body=[TextNode("Figure content")],
    )
    assert env_with_args != EnvironmentNode(
        name="figure",
        opt_args=[BracketNode([TextNode("HTB")])],
        args=[BraceNode([TextNode("0.8\\textwidth")])],
        body=[TextNode("Figure content")],
    )
    assert env_with_args != EnvironmentNode(
        name="figure",
        opt_args=[BracketNode([TextNode("HTB")])],
        args=[BraceNode([TextNode("0.8")])],
        body=[TextNode("Figure content")],
    )

    # Test with nested environments
    nested_env = EnvironmentNode(
        name="outer",
        opt_args=[],
        args=[],
        body=[
            EnvironmentNode(
                name="inner",
                opt_args=[],
                args=[],
                body=[TextNode("Nested content")],
            )
        ],
    )
    assert nested_env == EnvironmentNode(
        name="outer",
        opt_args=[],
        args=[],
        body=[
            EnvironmentNode(
                name="inner",
                opt_args=[],
                args=[],
                body=[TextNode("Nested content")],
            )
        ],
    )
    assert nested_env != EnvironmentNode(
        name="outer",
        opt_args=[],
        args=[],
        body=[
            EnvironmentNode(
                name="inner",
                opt_args=[],
                args=[],
                body=[TextNode("Different nested content")],
            )
        ],
    )
