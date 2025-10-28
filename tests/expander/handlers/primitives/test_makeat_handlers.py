from latex2json.expander.expander import Expander
from latex2json.tokens.catcodes import Catcode


def test_makeatletter_makeatother():
    r"""Test \makeatletter and \makeatother commands"""
    expander = Expander()

    # Before makeatletter, @ should be OTHER (catcode 12)
    assert expander.state.get_catcode(ord("@")) == Catcode.OTHER

    # After makeatletter, @ should be LETTER (catcode 11)
    expander.expand(r"\makeatletter")
    assert expander.state.get_catcode(ord("@")) == Catcode.LETTER

    # After makeatother, @ should be back to OTHER (catcode 12)
    expander.expand(r"\makeatother")
    assert expander.state.get_catcode(ord("@")) == Catcode.OTHER


def test_at_makeletter():
    r"""Test \@makeletter\X to set character X to catcode 11 (letter)"""
    expander = Expander()

    # Need makeatletter first so @ is part of the command name
    expander.expand(r"\makeatletter")

    # Initially # should be PARAMETER (catcode 6)
    assert expander.state.get_catcode(ord("#")) == Catcode.PARAMETER

    # Use \@makeletter\# to make # a letter
    expander.expand(r"\@makeletter\#")
    assert expander.state.get_catcode(ord("#")) == Catcode.LETTER

    # Test with $ (initially MATH_SHIFT, catcode 3)
    assert expander.state.get_catcode(ord("$")) == Catcode.MATH_SHIFT
    expander.expand(r"\@makeletter\$")
    assert expander.state.get_catcode(ord("$")) == Catcode.LETTER


def test_at_makeother():
    r"""Test \@makeother\X to set character X to catcode 12 (other)"""
    expander = Expander()

    # Make @ a letter first so we can use \@makeother
    expander.expand(r"\makeatletter")
    assert expander.state.get_catcode(ord("@")) == Catcode.LETTER

    # Test with another character - make a letter character into other
    expander.expand(r"\@makeother\A")
    assert expander.state.get_catcode(ord("A")) == Catcode.OTHER

    # Make # a letter first, then change it to other
    expander.expand(r"\@makeletter\#")
    assert expander.state.get_catcode(ord("#")) == Catcode.LETTER
    expander.expand(r"\@makeother\#")
    assert expander.state.get_catcode(ord("#")) == Catcode.OTHER


def test_at_makeescape():
    r"""Test \@makeescape\X to set character X to catcode 0 (escape)"""
    expander = Expander()

    # Make @ a letter first so we can use \@makeescape
    expander.expand(r"\makeatletter")

    # By default, \ is ESCAPE (catcode 0)
    assert expander.state.get_catcode(ord("\\")) == Catcode.ESCAPE

    # Make £ an escape character
    expander.expand(r"\@makeescape\£")
    assert expander.state.get_catcode(ord("£")) == Catcode.ESCAPE


def test_make_commands_combined():
    r"""Test using multiple @make* commands together"""
    expander = Expander()

    text = r"""
    \makeatletter
    \@makeletter\#     % make # a letter
    \@makeother\#      % make # other again
    \@makeescape\£     % make £ an escape character
    """
    expander.expand(text)

    # After all operations, # should be OTHER
    assert expander.state.get_catcode(ord("#")) == Catcode.OTHER
    # £ should be ESCAPE
    assert expander.state.get_catcode(ord("£")) == Catcode.ESCAPE


def test_make_commands_with_whitespace():
    r"""Test that @make* commands handle whitespace properly"""
    expander = Expander()

    # Make @ a letter first
    expander.expand(r"\makeatletter")

    # Test with whitespace between command and character
    expander.expand(r"\@makeletter   \#")
    assert expander.state.get_catcode(ord("#")) == Catcode.LETTER

    expander.expand(r"\@makeother   \#")
    assert expander.state.get_catcode(ord("#")) == Catcode.OTHER
