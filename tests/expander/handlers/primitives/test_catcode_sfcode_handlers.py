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


def test_mathcode_with_backtick_syntax():
    r"""Test \mathcode with traditional backtick syntax - just verify parsing works"""
    expander = Expander()

    # Test \mathcode`\+=12345 (backtick syntax) - should parse without error
    result = expander.expand(r"\mathcode`\+=12345")
    assert result == []

    # Test \mathcode`\-=8000 (set minus sign)
    result = expander.expand(r"\mathcode`\-=8000")
    assert result == []


def test_mathcode_with_numeric_syntax():
    r"""Test \mathcode with numeric character codes - just verify parsing works"""
    expander = Expander()

    # Test \mathcode 65=1234 (set 'A' mathcode) - should parse without error
    result = expander.expand(r"\mathcode 65=1234")
    assert result == []

    # Test \mathcode 97=5678 (set 'a' mathcode)
    result = expander.expand(r"\mathcode 97=5678")
    assert result == []

    # Test with large value
    result = expander.expand(r"\mathcode 48=12345")
    assert result == []


def test_mathcode_without_equals():
    r"""Test \mathcode with optional equals sign"""
    expander = Expander()

    # Test without equals sign: \mathcode 66 9999 - should parse without error
    result = expander.expand(r"\mathcode 66 9999")
    assert result == []

    # Test with backtick but no equals: \mathcode`\* 11111
    result = expander.expand(r"\mathcode`\* 11111")
    assert result == []


def test_mathcode_mixed_usage():
    r"""Test mixing numeric and backtick syntax for mathcode"""
    expander = Expander()

    # Use numeric to set mathcode - should parse without error
    result = expander.expand(r"\mathcode 120=5000")
    assert result == []

    # Use backtick
    result = expander.expand(r"\mathcode`\x=6000")
    assert result == []

    # Use numeric without equals
    result = expander.expand(r"\mathcode 120 7000")
    assert result == []
