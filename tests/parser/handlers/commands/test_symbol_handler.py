import pytest
from latex2json.parser import Parser


@pytest.fixture
def parser():
    return Parser()


def test_symbol_hex_quote_prefix(parser):
    r"""Test symbol with hexadecimal using TeX-style " prefix."""
    text = r'\symbol{"0041}'
    result = parser.parse(text)
    assert parser.convert_nodes_to_str(result) == "A"


def test_symbol_decimal(parser):
    r"""Test symbol with decimal number."""
    text = r'\symbol{65}'
    result = parser.parse(text)
    assert parser.convert_nodes_to_str(result) == "A"


def test_symbol_octal_quote_prefix(parser):
    r"""Test symbol with octal using TeX-style ' prefix."""
    text = r"\symbol{'101}"
    result = parser.parse(text)
    assert parser.convert_nodes_to_str(result) == "A"


def test_symbol_multiple_in_text(parser):
    r"""Test multiple symbol commands in text."""
    text = r'Hello \symbol{65}\symbol{66}\symbol{67}!'
    result = parser.parse(text)
    assert parser.convert_nodes_to_str(result) == "Hello ABC!"


def test_usym_basic(parser):
    r"""Test usym with basic hex codepoint."""
    text = r'\usym{0041}'
    result = parser.parse(text)
    assert parser.convert_nodes_to_str(result) == "A"


def test_usym_emoji(parser):
    r"""Test usym with emoji codepoint."""
    text = r'\usym{1F642}'
    result = parser.parse(text)
    assert parser.convert_nodes_to_str(result) == "🙂"


def test_usym_greek(parser):
    r"""Test usym with Greek alpha."""
    text = r'\usym{03B1}'
    result = parser.parse(text)
    assert parser.convert_nodes_to_str(result) == "α"


def test_char_decimal(parser):
    r"""Test char with decimal number."""
    text = r'\char65'
    result = parser.parse(text)
    assert parser.convert_nodes_to_str(result) == "A"


def test_char_hex(parser):
    r"""Test char with hexadecimal using " prefix."""
    text = r'\char"0041'
    result = parser.parse(text)
    assert parser.convert_nodes_to_str(result) == "A"


def test_char_octal(parser):
    r"""Test char with octal using ' prefix."""
    text = r"\char'101"
    result = parser.parse(text)
    assert parser.convert_nodes_to_str(result) == "A"
