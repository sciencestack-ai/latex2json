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
    \NewDocumentCommand {\greetTwo} {m m}{Hello #1 and #2!}
    """.strip()
    expander.expand(text)
    assert_token_sequence(
        expander.expand(r"\greetTwo{Alice}{Bob}"),
        expander.expand("Hello Alice and Bob!"),
    )


def test_newdocumentcommand_with_star():
    """Test star argument (s) with IfBooleanTF."""
    expander = Expander()

    text = r"\NewDocumentCommand{\test}{s m}{\IfBooleanTF{#1} {Star}{No star}: #2}"
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

    # Without optional - NoValue sentinel is a CS token, not visible text
    result = expander.expand(r"\test{world}")
    result_str = expander.convert_tokens_to_str(result)
    assert "-NoValue-" not in result_str  # sentinel should NOT appear as text
    assert "Arg2: world" in result_str

    # With optional
    result = expander.expand(r"\test[hello]{world}")
    expected = expander.expand("Arg1: hello, Arg2: world")
    assert_token_sequence(result, expected)


def test_ifboolean_t_and_f():
    """Test IfBooleanT and IfBooleanF commands."""
    expander = Expander()

    # Test IfBooleanT
    text = (
        r"\NewDocumentCommand{\testT} {s m} {\IfBooleanT {#1}{Star detected!} Arg: #2}"
    )
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
    assert_token_sequence(expander.expand(r"\test{hi}"), expander.expand("First: hi"))

    # Redefine it
    expander.expand(r"\RenewDocumentCommand{\test}{m}{Second: #1}")
    assert_token_sequence(expander.expand(r"\test{hi}"), expander.expand("Second: hi"))


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


def test_embellishment_no_subscript_or_superscript():
    """Test e{_^} with no subscript or superscript."""
    expander = Expander()

    expander.expand(
        r"""
        \NewDocumentCommand{\grad}{e{_^}}{%
          \nabla
          \IfValueT{#1}{_{#1}}%
          \IfValueT{#2}{^{#2}}%
        }
        """
    )

    result = expander.expand(r"\grad")
    result_str = "".join(tok.value for tok in result if tok.value.strip())

    # Should only have nabla, no subscript or superscript
    assert "nabla" in result_str
    assert "_" not in result_str
    assert "^" not in result_str


def test_embellishment_subscript_only():
    """Test e{_^} with subscript only."""
    expander = Expander()

    expander.expand(
        r"""
        \NewDocumentCommand{\grad}{e{_^}}{%
          \nabla
          \IfValueT{#1}{_{#1}}%
          \IfValueT{#2}{^{#2}}%
        }
        """
    )

    result = expander.expand(r"\grad_x")
    result_str = "".join(tok.value for tok in result if tok.value.strip())

    # Should have nabla and subscript
    assert "nabla" in result_str
    assert "_{x}" in result_str
    assert "^" not in result_str


def test_embellishment_superscript_only():
    """Test e{_^} with superscript only."""
    expander = Expander()

    expander.expand(
        r"""
        \NewDocumentCommand{\grad}{e{_^}}{%
          \nabla
          \IfValueT{#1}{_{#1}}%
          \IfValueT{#2}{^{#2}}%
        }
        """
    )

    result = expander.expand(r"\grad^2")
    result_str = "".join(tok.value for tok in result if tok.value.strip())

    # Should have nabla and superscript
    assert "nabla" in result_str
    assert "_" not in result_str
    assert "^{2}" in result_str


def test_embellishment_both_subscript_and_superscript():
    """Test e{_^} with both subscript and superscript."""
    expander = Expander()

    expander.expand(
        r"""
        \NewDocumentCommand{\grad}{e{_^}}{%
          \nabla
          \IfValueT{#1}{_{#1}}%
          \IfValueT{#2}{^{#2}}%
        }
        """
    )

    result = expander.expand(r"\grad_x^2")
    result_str = "".join(tok.value for tok in result if tok.value.strip())

    # Should have nabla, subscript, and superscript
    assert "nabla" in result_str
    assert "_{x}" in result_str
    assert "^{2}" in result_str


def test_embellishment_complex_arguments():
    """Test e{_^} with complex braced arguments."""
    expander = Expander()

    expander.expand(
        r"""
        \NewDocumentCommand{\grad}{e{_^}}{%
          \nabla
          \IfValueT{#1}{_{#1}}%
          \IfValueT{#2}{^{#2}}%
        }
        """
    )

    result = expander.expand(r"\grad_{i,j}^{2}")
    result_str = "".join(tok.value for tok in result if tok.value.strip())

    # Should have nabla with complex subscript and superscript
    assert "nabla" in result_str
    assert "_{i,j}" in result_str or "_{{i,j}}" in result_str
    assert "^{2}" in result_str


def test_ifvalue_with_novalue():
    """Test IfValue conditionals with -NoValue- marker."""
    expander = Expander()

    expander.expand(
        r"""
        \NewDocumentCommand{\test}{o m}{%
          \IfValueTF{#1}{HAS:#1}{NO}:%
          #2%
        }
        """
    )

    # Without optional argument
    result1 = expander.expand(r"\test{world}")
    result1_str = "".join(tok.value for tok in result1 if tok.value.strip())
    assert "NO:world" in result1_str

    # With optional argument
    result2 = expander.expand(r"\test[hello]{world}")
    result2_str = "".join(tok.value for tok in result2 if tok.value.strip())
    assert "HAS:hello:world" in result2_str


def test_ifnovalue_tf():
    r"""Test \IfNoValueTF — inverse of \IfValueTF."""
    expander = Expander()

    expander.expand(
        r"""
        \NewDocumentCommand{\test}{o m}{%
          \IfNoValueTF{#1}{MISSING}{PRESENT:#1}:%
          #2%
        }
        """
    )

    # Without optional argument — should take true (MISSING) branch
    result = expander.expand(r"\test{world}")
    result_str = "".join(tok.value for tok in result if tok.value.strip())
    assert "MISSING:world" in result_str

    # With optional argument — should take false (PRESENT) branch
    result = expander.expand(r"\test[hello]{world}")
    result_str = "".join(tok.value for tok in result if tok.value.strip())
    assert "PRESENT:hello:world" in result_str


def test_ifnovalue_t():
    r"""Test \IfNoValueT — only executes when arg is missing."""
    expander = Expander()

    expander.expand(
        r"\NewDocumentCommand{\test}{o m}{\IfNoValueT{#1}{DEFAULT} #2}"
    )

    result = expander.expand(r"\test{world}")
    result_str = expander.convert_tokens_to_str(result)
    assert "DEFAULT" in result_str

    result = expander.expand(r"\test[given]{world}")
    result_str = expander.convert_tokens_to_str(result)
    assert "DEFAULT" not in result_str
    assert "world" in result_str


def test_ifnovalue_f():
    r"""Test \IfNoValueF — only executes when arg is present."""
    expander = Expander()

    expander.expand(
        r"\NewDocumentCommand{\test}{o m}{\IfNoValueF{#1}{HAS:#1} #2}"
    )

    # Without optional — F branch should NOT fire
    result = expander.expand(r"\test{world}")
    result_str = expander.convert_tokens_to_str(result)
    assert "HAS:" not in result_str

    # With optional — F branch should fire
    result = expander.expand(r"\test[val]{world}")
    result_str = expander.convert_tokens_to_str(result)
    assert "HAS:val" in result_str


def test_embellishment_order_in_spec():
    """Test that e{_^} assigns #1 to _ and #2 to ^, regardless of input order."""
    expander = Expander()

    expander.expand(
        r"""
        \NewDocumentCommand{\test}{e{_^}}{%
          \IfValueT{#1}{SUB:#1}%
          \IfValueT{#2}{SUP:#2}%
        }
        """
    )

    # Standard order: _ then ^
    result1 = expander.expand(r"\test_{b}^{a}")
    result1_str = "".join(tok.value for tok in result1 if tok.value.strip())
    assert "SUB:b" in result1_str or "SUB:{b}" in result1_str
    assert "SUP:a" in result1_str or "SUP:{a}" in result1_str

    # Reversed order: ^ then _ (should still work)
    result2 = expander.expand(r"\test^{a}_{b}")
    result2_str = "".join(tok.value for tok in result2 if tok.value.strip())
    # #1 should be subscript (b), #2 should be superscript (a)
    # even though ^ appears first in the input
    assert "SUB:b" in result2_str or "SUB:{b}" in result2_str
    assert "SUP:a" in result2_str or "SUP:{a}" in result2_str


def test_ifnovalue_with_empty_branches():
    r"""Regression: \IfNoValueTF with empty true/false branches must not leak sentinel.

    When a branch is {}, parse_immediate_token returns [] (empty list).
    The handlers must check `is None` not truthiness, or they bail early
    and leak \q__xparse_no_value into the output.
    """
    expander = Expander()

    # Pattern from rec-thy.sty: \Oleq has empty true branch
    expander.expand(
        r"\NewDocumentCommand{\Oleq}{o}{\leq_{\mathcal{O}\IfNoValueTF{#1}{}{,#1}}}"
    )

    # Without optional arg: true branch is empty {}, sentinel must NOT leak
    result = expander.expand(r"\Oleq")
    result_str = "".join(tok.value for tok in result)
    assert "q__xparse_no_value" not in result_str
    assert ",," not in result_str  # no stray comma either

    # With optional arg: false branch produces ,#1
    result = expander.expand(r"\Oleq[x]")
    result_str = "".join(tok.value for tok in result)
    assert ",x" in result_str
    assert "q__xparse_no_value" not in result_str


def test_ifvalue_with_empty_branches():
    r"""Regression: \IfValueTF with empty branches must work correctly."""
    expander = Expander()

    expander.expand(
        r"\NewDocumentCommand{\test}{o m}{\IfValueTF{#1}{}{FALLBACK}#2}"
    )

    # Without optional: should get FALLBACK (false branch)
    result = expander.expand(r"\test{ok}")
    result_str = "".join(tok.value for tok in result if tok.value.strip())
    assert "FALLBACK" in result_str

    # With optional: true branch is empty {}, should just get #2
    result = expander.expand(r"\test[hi]{ok}")
    result_str = "".join(tok.value for tok in result if tok.value.strip())
    assert "FALLBACK" not in result_str
    assert "ok" in result_str
