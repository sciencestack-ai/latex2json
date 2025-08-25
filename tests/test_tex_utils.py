from latex2json.utils.tex_utils import parse_key_val_string


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
