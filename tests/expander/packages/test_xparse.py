from latex2json.expander.expander import Expander
from tests.test_utils import assert_token_sequence


def test_newdocumentcommand_basic():
    """Test basic NewDocumentCommand with mandatory arguments."""
    expander = Expander()

    # Basic command with one mandatory argument
    text = r"""
    \NewDocumentCommand{\greet}{m}{Hello #1!}
    """.strip()
    expander.expand(text)
    assert expander.get_macro("\\greet")
    assert_token_sequence(
        expander.expand(r"\greet{world}"), expander.expand("Hello world!")
    )

    # Command with two mandatory arguments
    text = r"""
    \NewDocumentCommand{\greetTwo}{m m}{Hello #1 and #2!}
    """.strip()
    expander.expand(text)
    assert_token_sequence(
        expander.expand(r"\greetTwo{Alice}{Bob}"), expander.expand("Hello Alice and Bob!")
    )


def test_newdocumentcommand_with_star():
    """Test star argument (s) with IfBooleanTF."""
    expander = Expander()

    text = r"\NewDocumentCommand{\test}{s m}{\IfBooleanTF{#1}{Star}{No star}: #2}"
    expander.expand(text)
    assert expander.get_macro("\\test")

    # Without star
    result = expander.expand(r"\test{world}")
    expected = expander.expand("No star: world")
    assert_token_sequence(result, expected)

    # With star
    result = expander.expand(r"\test*{world}")
    expected = expander.expand("Star: world")
    assert_token_sequence(result, expected)


def test_newdocumentcommand_optional_with_default():
    """Test optional argument with default (O{default})."""
    expander = Expander()

    text = r"""
    \NewDocumentCommand{\greet}{O{friend} m}{Hello #1 and #2!}
    """.strip()
    expander.expand(text)

    # Without optional argument - use default
    result = expander.expand(r"\greet{world}")
    expected = expander.expand("Hello friend and world!")
    assert_token_sequence(result, expected)

    # With optional argument
    result = expander.expand(r"\greet[Alice]{world}")
    expected = expander.expand("Hello Alice and world!")
    assert_token_sequence(result, expected)


def test_newdocumentcommand_combined():
    """Test the example from the user: star + optional + mandatory."""
    expander = Expander()

    text = r"\NewDocumentCommand{\test}{s O{default} m}{\IfBooleanTF{#1}{Star}{No star}: #2 and #3}"
    expander.expand(text)
    assert expander.get_macro("\\test")

    # Without star, without optional
    result = expander.expand(r"\test{world}")
    expected = expander.expand("No star: default and world")
    assert_token_sequence(result, expected)

    # Without star, with optional
    result = expander.expand(r"\test[hello]{world}")
    expected = expander.expand("No star: hello and world")
    assert_token_sequence(result, expected)

    # With star, without optional
    result = expander.expand(r"\test*{world}")
    expected = expander.expand("Star: default and world")
    assert_token_sequence(result, expected)

    # With star, with optional
    result = expander.expand(r"\test*[hello]{world}")
    expected = expander.expand("Star: hello and world")
    assert_token_sequence(result, expected)


def test_newdocumentcommand_optional_no_default():
    """Test optional argument without default (o)."""
    expander = Expander()

    text = r"\NewDocumentCommand{\test}{o m}{Arg1: #1, Arg2: #2}"
    expander.expand(text)

    # Without optional - should get -NoValue-
    result = expander.expand(r"\test{world}")
    result_str = expander.convert_tokens_to_str(result)
    assert "Arg1: -NoValue-" in result_str
    assert "Arg2: world" in result_str

    # With optional
    result = expander.expand(r"\test[hello]{world}")
    expected = expander.expand("Arg1: hello, Arg2: world")
    assert_token_sequence(result, expected)


def test_ifboolean_t_and_f():
    """Test IfBooleanT and IfBooleanF commands."""
    expander = Expander()

    # Test IfBooleanT
    text = r"\NewDocumentCommand{\testT}{s m}{\IfBooleanT{#1}{Star detected!} Arg: #2}"
    expander.expand(text)

    result = expander.expand(r"\testT{world}")
    expected = expander.expand(" Arg: world")
    assert_token_sequence(result, expected)

    result = expander.expand(r"\testT*{world}")
    expected = expander.expand("Star detected! Arg: world")
    assert_token_sequence(result, expected)

    # Test IfBooleanF
    text = r"\NewDocumentCommand{\testF}{s m}{\IfBooleanF{#1}{No star!} Arg: #2}"
    expander.expand(text)

    result = expander.expand(r"\testF{world}")
    expected = expander.expand("No star! Arg: world")
    assert_token_sequence(result, expected)

    result = expander.expand(r"\testF*{world}")
    expected = expander.expand(" Arg: world")
    assert_token_sequence(result, expected)


def test_renewdocumentcommand():
    """Test RenewDocumentCommand."""
    expander = Expander()

    # Define a command
    expander.expand(r"\NewDocumentCommand{\test}{m}{First: #1}")
    assert_token_sequence(
        expander.expand(r"\test{hi}"), expander.expand("First: hi")
    )

    # Redefine it
    expander.expand(r"\RenewDocumentCommand{\test}{m}{Second: #1}")
    assert_token_sequence(
        expander.expand(r"\test{hi}"), expander.expand("Second: hi")
    )


def test_newdocumentcommand_multiple_args():
    """Test command with many arguments."""
    expander = Expander()

    text = r"\NewDocumentCommand{\test}{m m m m}{#1-#2-#3-#4}"
    expander.expand(text)

    result = expander.expand(r"\test{A}{B}{C}{D}")
    expected = expander.expand("A-B-C-D")
    assert_token_sequence(result, expected)


def test_newdocumentcommand_nested():
    """Test nested NewDocumentCommand definitions."""
    expander = Expander()

    text = r"\NewDocumentCommand{\outer}{m}{\NewDocumentCommand{\inner}{m}{Outer: #1, Inner: ##1}}"
    expander.expand(text)

    assert expander.get_macro("\\outer")
    assert not expander.get_macro("\\inner")  # Not created yet

    expander.expand(r"\outer{OUTER_ARG}")
    assert expander.get_macro("\\inner")  # Now created

    result = expander.expand(r"\inner{INNER_ARG}")
    expected = expander.expand("Outer: OUTER_ARG, Inner: INNER_ARG")
    assert_token_sequence(result, expected)


def test_newdocumentcommand_scope():
    """Test that NewDocumentCommand is global."""
    expander = Expander()

    text = r"""
    {
        \NewDocumentCommand{\local}{m}{Local: #1}
    }
    """.strip()
    expander.expand(text)

    # Should be global
    assert expander.get_macro("\\local")
    result = expander.expand(r"\local{test}")
    expected = expander.expand("Local: test")
    assert_token_sequence(result, expected)


def test_declaredocumentcommand():
    """Test DeclareDocumentCommand alias."""
    expander = Expander()

    expander.expand(r"\DeclareDocumentCommand{\test}{m}{Declared: #1}")
    assert expander.get_macro("\\test")
    assert_token_sequence(
        expander.expand(r"\test{hi}"), expander.expand("Declared: hi")
    )


def test_providedocumentcommand():
    """Test ProvideDocumentCommand alias."""
    expander = Expander()

    expander.expand(r"\ProvideDocumentCommand{\test}{m}{Provided: #1}")
    assert expander.get_macro("\\test")
    assert_token_sequence(
        expander.expand(r"\test{hi}"), expander.expand("Provided: hi")
    )
