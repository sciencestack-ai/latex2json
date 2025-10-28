from latex2json.expander.expander import Expander
from latex2json.tokens.catcodes import Catcode


def test_catcode_with_backtick_syntax():
    r"""Test \catcode with traditional backtick syntax"""
    expander = Expander()

    # Test \catcode`\@=11 (backtick syntax)
    expander.expand(r"\catcode`\@=11")
    assert expander.state.get_catcode(ord("@")) == Catcode.LETTER

    # Test \catcode`\#=12 (make # other)
    expander.expand(r"\catcode`\#=12")
    assert expander.state.get_catcode(ord("#")) == Catcode.OTHER


def test_catcode_with_numeric_syntax():
    r"""Test \catcode with numeric character codes"""
    expander = Expander()

    # Test \catcode 96=12 (set backtick to OTHER)
    expander.expand(r"\catcode 96=12")
    assert expander.state.get_catcode(96) == Catcode.OTHER

    # Test \catcode 61=12 (set equals to OTHER)
    expander.expand(r"\catcode 61=12")
    assert expander.state.get_catcode(61) == Catcode.OTHER

    # Test \catcode 64=11 (set @ to LETTER)
    expander.expand(r"\catcode 64=11")
    assert expander.state.get_catcode(64) == Catcode.LETTER


def test_catcode_without_equals():
    r"""Test \catcode with optional equals sign"""
    expander = Expander()

    # Test without equals sign: \catcode 65 12 (set 'A' to OTHER)
    expander.expand(r"\catcode 65 12")
    assert expander.state.get_catcode(65) == Catcode.OTHER

    # Test with backtick but no equals: \catcode`\$ 12
    expander.expand(r"\catcode`\$ 12")
    assert expander.state.get_catcode(ord("$")) == Catcode.OTHER


def test_catcode_mixed_usage():
    r"""Test mixing numeric and backtick syntax"""
    expander = Expander()

    # Use numeric to set @ to letter
    expander.expand(r"\catcode 64=11")
    assert expander.state.get_catcode(ord("@")) == Catcode.LETTER

    # Use backtick to set it back to other
    expander.expand(r"\catcode`\@=12")
    assert expander.state.get_catcode(ord("@")) == Catcode.OTHER

    # Use numeric without equals
    expander.expand(r"\catcode 64 11")
    assert expander.state.get_catcode(ord("@")) == Catcode.LETTER
