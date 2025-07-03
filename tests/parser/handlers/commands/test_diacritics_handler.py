import pytest

from latex2json.nodes import CommandNode, TextNode
from latex2json.parser.parser import Parser


def test_diacritics():
    parser = Parser()

    def convert_tex_diacritics(text: str) -> str:
        out = parser.parse(text)
        assert len(out) == 1 and isinstance(out[0], TextNode)
        return out[0].text

    # Test vector accent with different formats
    assert convert_tex_diacritics(r"\vec {x}") == "x⃗"
    assert convert_tex_diacritics(r"\vec x") == "x⃗"
    assert convert_tex_diacritics(r"\vec3") == "3⃗"

    # Test multiple vector accents in one string
    assert convert_tex_diacritics(r"\vec{x}\vec y\vec3") == "x⃗y⃗3⃗"

    # Test with numbers and other characters
    assert convert_tex_diacritics(r"\vec333") == "3⃗33"
    assert convert_tex_diacritics(r"\vec{333}") == "3⃗33"
    assert convert_tex_diacritics(r"\vec{ 333}") == "3⃗33"

    # Test with ^~=`'"
    assert convert_tex_diacritics(r"\^{abb}") == "âbb"
    assert convert_tex_diacritics(r"\~a") == "ã"
    assert convert_tex_diacritics(r"\=a") == "ā"
    assert convert_tex_diacritics(r"\'a") == "á"
    assert convert_tex_diacritics(r"\`{abb}") == "àbb"
    assert convert_tex_diacritics(r"\"a") == "ä"

    # Test basic accents
    assert convert_tex_diacritics(r"\'a") == "á"
    assert convert_tex_diacritics(r"\`a") == "à"
    assert convert_tex_diacritics(r"\"a") == "ä"
    assert convert_tex_diacritics(r"\^a") == "â"
    assert convert_tex_diacritics(r"\~a") == "ã"
    assert convert_tex_diacritics(r"\=a") == "ā"

    # Test special letters
    assert convert_tex_diacritics(r"\c{c}") == "ç"
    assert convert_tex_diacritics(r"\v{s}") == "š"
    assert convert_tex_diacritics(r"\H{o}") == "ő"
    assert convert_tex_diacritics(r"\k{a}") == "ą"
    assert convert_tex_diacritics(r"\b{a}") == "a̱"
    assert convert_tex_diacritics(r"\.{a}") == "ȧ"
    assert convert_tex_diacritics(r"\d{a}") == "ạ"
    assert convert_tex_diacritics(r"\r{a}") == "å"
    assert convert_tex_diacritics(r"\u{a}") == "ă"
    assert convert_tex_diacritics(r"\u00a7") == "0̆0a7"

    # Test extended commands
    assert convert_tex_diacritics(r"\dot{x}") == "ẋ"
    assert convert_tex_diacritics(r"\hat{x}") == "x̂"
    assert convert_tex_diacritics(r"\check{xeee}") == "x̌eee"
    assert convert_tex_diacritics(r"\breve{x}") == "x̆"
    assert convert_tex_diacritics(r"\acute{x}fff") == "x́fff"
    assert convert_tex_diacritics(r"\grave{x}") == "x̀"
    assert convert_tex_diacritics(r"\tilde{x}") == "x̃"
    assert convert_tex_diacritics(r"\bar{x}") == "x̅"
    assert convert_tex_diacritics(r"\ddot{x}") == "ẍ"

    # Test special
    assert convert_tex_diacritics(r"\not{=}") == "≠"

    # Test combinations and spacing variants
    assert convert_tex_diacritics(r"\.{i}") == "i̇"
    assert convert_tex_diacritics(r"\. i") == "i̇"
