import os
from latex2json.utils.tex_utils import parse_key_val_string, strip_latex_comments


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
