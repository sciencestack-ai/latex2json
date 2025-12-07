r"""Test \import and \subimport commands from the import package."""
import pytest
import os

from latex2json.tex_reader import TexReader


dir_path = os.path.dirname(os.path.abspath(__file__))
samples_dir_path = os.path.join(dir_path, "samples")


def test_import_and_subimport():
    r"""Test that \import and \subimport correctly handle nested file imports.

    Structure:
    - main.tex uses \import{sections/}{intro.tex}
    - sections/intro.tex uses \subimport{figs/}{figurecaption.tex}
    - sections/figs/figurecaption.tex contains text

    The \subimport path is relative to sections/ (where intro.tex is),
    not to the main directory.
    """
    tex_reader = TexReader()

    output = tex_reader.process(samples_dir_path + "/import_test")
    json_output = tex_reader.to_json(output)

    assert len(json_output) >= 1
    assert output.tokens is not None
    assert len(output.tokens) > 0

    # Helper to recursively search for text in tokens
    def find_text(tokens, search_text):
        if not isinstance(tokens, list):
            return False
        for token in tokens:
            if not isinstance(token, dict):
                continue
            if token.get("type") == "text":
                content = token.get("content", "")
                if search_text in content:
                    return True
            if "content" in token and isinstance(token["content"], list):
                if find_text(token["content"], search_text):
                    return True
        return False

    # Verify all three files were loaded
    assert find_text(output.tokens, "This is the main file"), \
        "Main file content should be present"

    assert find_text(output.tokens, "This is intro from sections/intro.tex"), \
        "Content from \\import{sections/}{intro.tex} should be present"

    assert find_text(output.tokens, "Caption goes here from sections/figs/figurecaption.tex"), \
        "Content from \\subimport{figs/}{figurecaption.tex} should be present"
