import os
from latex2json.utils.tex_utils import (
    parse_key_val_string,
    strip_latex_comments,
    convert_color_to_css,
)


def test_parse_key_val_string():
    # Test simple key-value pairs
    assert parse_key_val_string("name=Theorem") == {"name": "Theorem"}
    assert parse_key_val_string("name=Theorem,numbered=no") == {
        "name": "Theorem",
        "numbered": "no",
    }

    # Test with braces
    assert parse_key_val_string("name={My Theorem}") == {"name": "{My Theorem}"}
    assert parse_key_val_string("Refname={Theorem,Theorems}") == {
        "Refname": "{Theorem,Theorems}"
    }

    # Test complex options
    options = "name=Definition,Refname={Definition,Definitions},sibling=thm"
    expected = {
        "name": "Definition",
        "Refname": "Definition,Definitions",
        "sibling": "thm",
    }
    assert parse_key_val_string(options, include_braces=False) == expected

    # Test nested braces
    assert parse_key_val_string("name={{Nested} Theorem}", include_braces=False) == {
        "name": "Nested Theorem"
    }

    # Test empty options
    assert parse_key_val_string("") == {}
    assert parse_key_val_string("key=") == {"key": ""}


def test_strip_latex_comments():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_file = os.path.join(current_dir, "sample_comments.tex")
    with open(sample_file, "r") as f:
        content = f.read()
    content = strip_latex_comments(content.strip())
    # no line should be empty/whitespace-only within the context of this file
    # where % ... are stripped entirely without trailing \n
    assert all(
        line.strip() for line in content.splitlines()
    ), "Content should not have any empty lines"


def test_convert_color_to_css():
    # Test rgb model (0-1 floats)
    assert convert_color_to_css("rgb", "0.2, 0.4, 0.8") == "rgb(51,102,204)"
    assert convert_color_to_css("rgb", "1.0, 0.0, 0.5") == "rgb(255,0,128)"
    assert convert_color_to_css("rgb", "0, 0, 0") == "rgb(0,0,0)"

    # Test RGB model with integers (0-255)
    assert convert_color_to_css("RGB", "255, 100, 50") == "rgb(255,100,50)"
    assert convert_color_to_css("RGB", "0, 128, 255") == "rgb(0,128,255)"

    # Test RGB model with floats (0-1) - this is the new case
    assert convert_color_to_css("RGB", "0.5, 0.8, 0.2") == "rgb(128,204,51)"
    assert convert_color_to_css("RGB", "1.0, 0.0, 0.5") == "rgb(255,0,128)"
    assert convert_color_to_css("RGB", "0.0, 0.0, 0.0") == "rgb(0,0,0)"

    # Test HTML model
    assert convert_color_to_css("HTML", "FF6432") == "#FF6432"
    assert convert_color_to_css("HTML", "2E8B57") == "#2E8B57"

    # Test CMYK model
    assert convert_color_to_css("cmyk", "0.5, 0.8, 0, 0.2") == "rgb(102,40,204)"
    assert convert_color_to_css("CMYK", "0, 0, 0, 0") == "rgb(255,255,255)"

    # Test gray/grey model
    assert convert_color_to_css("gray", "0.7") == "rgb(178,178,178)"
    assert convert_color_to_css("grey", "0.5") == "rgb(128,128,128)"
    assert convert_color_to_css("gray", "0.0") == "rgb(0,0,0)"

    # Test HSB model
    assert convert_color_to_css("hsb", "0.6, 0.8, 0.9") == "rgb(46,119,230)"
    assert convert_color_to_css("hsb", "0.0, 0.0, 1.0") == "rgb(255,255,255)"

    # Test unknown model
    assert convert_color_to_css("unknown", "anything") == "black"
