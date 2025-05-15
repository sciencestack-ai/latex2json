import pytest
from typing import List

from latex2json.nodes import (
    ASTNode,
    EnvironmentNode,
    MathShiftNode,
    DimensionNode,
    ArgNode,
    BraceNode,
    BracketNode,
    CommandNode,
    EndOfLineNode,
    TextNode,
)
from latex2json.tokens import Tokenizer, TokenType, Catcode, Token
from latex2json.parser import ParserCore


def assert_ast_sequence(asts: List[ASTNode], expected_sequence: List[ASTNode]):
    assert len(asts) == len(expected_sequence)
    for ast, expected in zip(asts, expected_sequence):
        assert ast == expected


def test_parser_core():
    tokenizer = Tokenizer()
    text = r"""
\begin{document \cmd}[opt] % comment
\end{document}
    """.strip()

    parser = ParserCore(tokenizer)
    asts = parser.parse_text(text)
    expected_asts = [
        CommandNode(r"\begin"),
        BraceNode([TextNode("document"), TextNode(" "), CommandNode(r"\cmd")]),
        BracketNode([TextNode("opt")]),
        TextNode(" "),
        EndOfLineNode(),
        CommandNode(r"\end"),
        BraceNode([TextNode("document")]),
    ]
    assert_ast_sequence(asts, expected_asts)

    # argnodes
    text = r"\newcommand{\cmd}[1]{##12}"
    asts = parser.parse_text(text)
    expected_asts = [
        CommandNode(r"\newcommand"),
        BraceNode([CommandNode(r"\cmd")]),
        BracketNode([TextNode("1")]),
        BraceNode([ArgNode(12, num_params=2)]),
    ]
    assert_ast_sequence(asts, expected_asts)


def test_whitespace_and_match():
    tokenizer = Tokenizer()
    parser = ParserCore(tokenizer)

    # test that all whitespace gets merged to single token
    text = r"""  Hi  % Hi surrounded by 2 whitespaces both sides
"""
    asts = parser.parse_text(text)
    expected_asts = [TextNode("  "), TextNode("Hi"), TextNode("  "), EndOfLineNode()]
    assert_ast_sequence(asts, expected_asts)

    parser.set_text(r" \cmd @")
    assert parser.match(TokenType.CONTROL_SEQUENCE, value="cmd")
    parser.consume()
    assert parser.match(TokenType.CHARACTER, value="@")  # , catcode=Catcode.OTHER)
    assert parser.match(TokenType.CHARACTER, value="@", catcode=Catcode.OTHER)

    # now let's test setting the catcode of \ to WHITESPACE!
    tokenizer.set_catcode(ord("\\"), Catcode.SPACE)
    parser.set_text(r"\cmd @")
    assert parser.peek() == Token(
        type=TokenType.CHARACTER, value="\\", catcode=Catcode.SPACE, position=0
    )
    # \ is now skipped with match!
    assert parser.match(TokenType.CHARACTER, value="c")
    parser.consume()
    # assert parser.match(TokenType.CHARACTER, value="@")  # , catcode=Catcode.OTHER)
    # assert parser.match(TokenType.CHARACTER, value="@", catcode=Catcode.OTHER)


def test_malformed_braces_brackets():
    tokenizer = Tokenizer()
    text = r"{]\@#["

    # malformed braces and brackets are parsed as text nodes
    parser = ParserCore(tokenizer)
    asts = parser.parse_text(text)
    expected_asts = [
        TextNode("{"),
        TextNode("]"),
        CommandNode(r"\@"),
        TextNode("#"),
        TextNode("["),
    ]
    assert_ast_sequence(asts, expected_asts)

    # test catcode change of braces
    text = "{sdsds}"
    asts = parser.parse_text(text)
    expected_asts = [BraceNode([TextNode("sdsds")])]
    assert_ast_sequence(asts, expected_asts)

    # now change catcode to LETTER
    # now all become a single textnode
    parser.tokenizer.set_catcode(ord("{"), Catcode.LETTER)
    parser.tokenizer.set_catcode(ord("}"), Catcode.LETTER)
    asts = parser.parse_text(text)
    expected_asts = [TextNode(text)]
    assert_ast_sequence(asts, expected_asts)


def test_parameters_hash():
    tokenizer = Tokenizer()
    parser = ParserCore(tokenizer)
    asts = parser.parse_text("####2")
    expected_asts = [
        ArgNode(2, num_params=4),
    ]
    assert_ast_sequence(asts, expected_asts)

    # fallback string if no number
    asts = parser.parse_text("###")
    expected_asts = [
        TextNode("###"),
    ]
    assert_ast_sequence(asts, expected_asts)

    # ensure separated hash with whitespace is not ArgNode
    asts = parser.parse_text("## 1")
    expected_asts = [
        TextNode("##"),
        TextNode(" "),
        TextNode("1"),
    ]
    assert_ast_sequence(asts, expected_asts)

    # what if we change the catcode of # to LETTER?
    tokenizer.set_catcode(ord("#"), Catcode.LETTER)
    asts = parser.parse_text("###1")
    expected_asts = [
        TextNode("###1"),
    ]
    assert_ast_sequence(asts, expected_asts)

    # let's try changing @ to PARAMETER
    tokenizer.set_catcode(ord("@"), Catcode.PARAMETER)
    text = "@@2"
    asts = parser.parse_text(text)
    expected_asts = [
        ArgNode(2, num_params=2),
    ]
    assert_ast_sequence(asts, expected_asts)

    # fallback string if no number
    text = "@@@"
    asts = parser.parse_text(text)
    expected_asts = [
        TextNode(text),
    ]
    assert_ast_sequence(asts, expected_asts)


def test_parse_immediate_token():
    tokenizer = Tokenizer()
    parser = ParserCore(tokenizer)

    text_ast_pairs = [
        ("{abc}2", BraceNode([TextNode("abc")])),
        (r"\cmd sss", CommandNode(r"\cmd")),
        ("abc", TextNode("a")),
        ("123", TextNode("1")),
        ("$333$", MathShiftNode("$")),
    ]

    for text, expected in text_ast_pairs:
        parser.set_text(text)
        assert parser.parse_immediate_token() == expected


def test_mock_makeatletter():
    tokenizer = Tokenizer()

    parser = ParserCore(tokenizer)

    text = r"""
    \makeatletter
    \def\@star{STAR}
    \@star % -> single commandnode \@star
    \makeatother
    \@star % -> this is NOT a single commandnode
    """.strip()

    parser.set_text(text)
    parser.parse_element() == CommandNode(r"\makeatletter")

    # mock \makeatletter by setting @ to LETTER
    tokenizer.set_catcode(ord("@"), Catcode.LETTER)

    parser.parse_element(skip_whitespace=True) == CommandNode(r"\def")
    parser.parse_element() == CommandNode(r"\@star")
    parser.parse_element() == BraceNode([TextNode("STAR")])
    # \@star is a single commandnode
    parser.parse_element(skip_whitespace=True) == CommandNode(r"\@star")

    # mock \makeatother by setting @ back to OTHER
    parser.parse_element(skip_whitespace=True) == CommandNode(r"\makeatother")
    tokenizer.set_catcode(ord("@"), Catcode.OTHER)

    # \@ and star are now split!
    parser.parse_element(skip_whitespace=True) == CommandNode(r"\@")
    assert parser.parse_element() == TextNode("star")

    parser.skip_whitespace()
    assert parser.eof()


def test_parse_environment():
    tokenizer = Tokenizer()
    parser = ParserCore(tokenizer)

    text = r"""
    \begin{document}[OPT1]{ARG1}BODY \cmd\end{document}
    """.strip()

    parser.set_text(text)

    env_node = parser.parse_environment()
    assert env_node == EnvironmentNode(
        name="document",
        opt_args=[BracketNode([TextNode("OPT1")])],
        args=[BraceNode([TextNode("ARG1")])],
        body=[TextNode("BODY"), TextNode(" "), CommandNode(r"\cmd")],
    )
    assert parser.eof()

    # check nested environments
    text = r"""
    \begin{document}\begin{itemize}\end{itemize}\end{document}
    """.strip()
    parser.set_text(text)
    env_node = parser.parse_environment()
    assert isinstance(env_node, EnvironmentNode)
    assert env_node.name == "document"
    assert len(env_node.body) == 1
    assert isinstance(env_node.body[0], EnvironmentNode)
    assert env_node.body[0].name == "itemize"
    assert len(env_node.body[0].body) == 0
    # assert env_node == EnvironmentNode(
    #     name="document",
    #     body=[EnvironmentNode(name="itemize", body=[])],
    # )


# test helper functions
def test_parse_int_float_arguments():
    tokenizer = Tokenizer()
    parser = ParserCore(tokenizer)

    parser.set_text("123 456")
    assert parser.parse_integer() == 123
    parser.skip_whitespace()
    assert parser.parse_integer() == 456

    parser.set_text("-10.234")
    assert parser.parse_integer() == -10

    parser.set_text(".333")
    assert parser.parse_integer() is None

    # test float
    parser.set_text("-123.456")
    assert parser.parse_float() == -123.456

    parser.set_text(".23fe")
    assert parser.parse_float() == 0.23


def test_equality_ops():
    tokenizer = Tokenizer()
    parser = ParserCore(tokenizer)

    parser.set_text(" =1")
    assert parser.parse_equals()
    assert parser.parse_integer() == 1
    parser.set_text(" s= ")
    assert not parser.parse_equals()

    # test changing catcode of = to LETTER
    tokenizer.set_catcode(ord("="), Catcode.LETTER)
    parser.set_text("=")
    assert not parser.parse_equals()
    assert parser.parse_element() == TextNode("=")

    # test angle brackets
    parser.set_text(" <")
    assert parser.parse_angle_brackets() == "<"

    parser.set_text(">")
    assert parser.parse_angle_brackets() == ">"

    parser.set_text(" s< ")
    assert not parser.parse_angle_brackets()

    parser.set_text(" s> ")
    assert not parser.parse_angle_brackets()

    # test changing catcode of < and > to LETTER
    tokenizer.set_catcode(ord("<"), Catcode.LETTER)
    tokenizer.set_catcode(ord(">"), Catcode.LETTER)
    parser.set_text("<")
    assert not parser.parse_angle_brackets()
    assert parser.parse_element() == TextNode("<")

    parser.set_text(">")
    assert not parser.parse_angle_brackets()
    assert parser.parse_element() == TextNode(">")


def test_parse_dimension():
    tokenizer = Tokenizer()
    parser = ParserCore(tokenizer)

    parser.set_text("123pt")
    assert parser.parse_dimension() == DimensionNode(123, "pt")

    parser.set_text("-0.3 cm")
    assert parser.parse_dimension() == DimensionNode(-0.3, "cm")


def test_parse_asterisk():
    tokenizer = Tokenizer()
    parser = ParserCore(tokenizer)

    parser.set_text("*1")
    assert parser.parse_asterisk()
    assert parser.parse_integer() == 1
