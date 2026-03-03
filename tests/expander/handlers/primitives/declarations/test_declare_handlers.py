import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token, TokenType


def test_declare_robust_command():
    expander = Expander()
    # Test basic declaration
    expander.expand(r"\DeclareRobustCommand{\testcmd}{test content}")
    assert expander.expand(r"\testcmd") == expander.expand("test content")

    # Test with star and parameters
    expander.expand(r"\DeclareRobustCommand*{\paramcmd}[2]{#1-#2}")
    assert expander.expand(r"\paramcmd{a}{b}") == expander.expand("a-b")

    assert expander.check_macro_is_user_defined("testcmd")
    assert expander.check_macro_is_user_defined("paramcmd")


def test_declare_math_operator():
    expander = Expander()
    # Test without star
    expander.expand(r"\DeclareMathOperator{\testop}{test}")
    tokens = expander.expand(r"\testop")
    tokens_str = expander.convert_tokens_to_str(tokens)
    assert "mathop" in tokens_str
    assert "mathrm" in tokens_str
    assert "nolimits" in tokens_str

    # Test with star
    expander.expand(r"\DeclareMathOperator*{\testopstar}{test}")
    tokens = expander.expand(r"\testopstar")
    tokens_str = expander.convert_tokens_to_str(tokens)
    assert tokens_str.endswith("limits")

    assert expander.check_macro_is_user_defined("testop")
    assert expander.check_macro_is_user_defined("testopstar")


def test_declare_paired_delimiter():
    expander = Expander()
    # Test basic delimiter
    expander.expand(r"\DeclarePairedDelimiter\testbr{(}{)}")
    tokens = expander.expand(r"\testbr{content}")
    assert tokens == expander.expand("(content)")

    assert expander.check_macro_is_user_defined("testbr")


def test_declare_ignored_commands():
    expander = Expander()
    # Test that ignored commands don't raise errors
    assert expander.expand(r"\DeclareFontFamily{T1}{cmr}{}") == []
    # DeclareMathSymbol and DeclareMathDelimiter are tested separately (they register passthroughs)
    assert expander.expand(r"\DeclareOption*{draft}") == []
    assert expander.expand(r"\DeclareOption{draft}{}") == []
    assert expander.expand(r"\DeclareGraphicsExtensions{pdf,png,jpg}") == []
    assert (
        expander.expand(
            r"\DeclareGraphicsRule{.tif}{png}{.png}{`convert #1 `basename #1 .tif`.png}"
        )
        == []
    )


def test_declare_math_symbol_registers_passthrough():
    """DeclareMathSymbol should register the command as a passthrough macro."""
    expander = Expander()
    # Declaration consumes all args and produces no output
    assert expander.expand(r"\DeclareMathSymbol{\boxdot}{0}{AMSa}{'00}") == []
    # The command should now be registered
    assert expander.get_macro("boxdot")
    assert expander.check_macro_is_user_defined("boxdot")
    # Using the command should produce itself as a control sequence token
    tokens = expander.expand(r"\boxdot")
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.CONTROL_SEQUENCE
    assert tokens[0].value == "boxdot"


def test_declare_math_delimiter_registers_passthrough():
    """DeclareMathDelimiter should register the command as a passthrough macro."""
    expander = Expander()
    # 6 args: \cmd, type, font1, slot1, font2, slot2
    assert (
        expander.expand(
            r"\DeclareMathDelimiter{\ulcorner}{4}{AMSa}{'70}{AMSa}{'70}"
        )
        == []
    )
    assert expander.get_macro("ulcorner")
    assert expander.check_macro_is_user_defined("ulcorner")
    tokens = expander.expand(r"\ulcorner")
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.CONTROL_SEQUENCE
    assert tokens[0].value == "ulcorner"


def test_declare_math_operator_invalid():
    expander = Expander()
    # Test missing command name
    expander.expand(r"\DeclareMathOperator{test}") == []
    assert not expander.get_macro("test")

    # Test missing definition
    expander.expand(r"\DeclareMathOperator\testop") == []
    assert not expander.get_macro("testop")


def test_declare_paired_delimiter_invalid():
    expander = Expander()
    # Test missing delimiters
    expander.expand(r"\DeclarePairedDelimiter\testbr{(}") == []
    assert not expander.get_macro("testbr")


def test_declare_textfont():
    expander = Expander()
    expander.expand(r"\DeclareTextFontCommand{\myfont}{\textbf}")
    assert expander.get_macro("myfont")
    assert expander.check_macro_is_user_defined("myfont")

    tokens = expander.expand(r"\myfont{Hello}")
    assert tokens == expander.expand(r"\textbf{Hello}")


def test_declare_fixedfont():
    expander = Expander()
    expander.expand(r"\DeclareFixedFont{\myfont}{rm}{m}{n}{10}")
    assert expander.get_macro("myfont")
    assert expander.check_macro_is_user_defined("myfont")

    # ignore?
    out_str = expander.convert_tokens_to_str(expander.expand(r"\myfont{Hello}"))
    assert out_str == "{Hello}"
