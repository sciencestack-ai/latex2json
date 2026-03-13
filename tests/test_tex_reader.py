import pytest
import os

from latex2json.tex_reader import TexReader


dir_path = os.path.dirname(os.path.abspath(__file__))
samples_dir_path = os.path.join(dir_path, "samples")


def test_process_text():
    tex_reader = TexReader()
    result = tex_reader.process_text(
        r"\begin{document}\section{Hello}Some \textbf{bold} text.\end{document}"
    )

    assert result.tokens is not None
    assert len(result.tokens) > 0
    assert result.main_tex_path is None
    assert result.project_root is None

    # Find the section
    doc = result.tokens[0]
    assert doc["type"] == "document"
    section = doc["content"][0]
    assert section["type"] == "section"
    assert section["title"][0]["content"] == "Hello"


def test_tex_reader():
    tex_reader = TexReader()

    # test working on subfiles
    output = tex_reader.process(samples_dir_path + "/subfiles")
    json_output = tex_reader.to_json(output)

    assert len(json_output) >= 1


def test_flt_file():
    """Test processing a .flt file"""
    tex_reader = TexReader()

    # test working with .flt file
    output = tex_reader.process(samples_dir_path + "/simple.flt")
    json_output = tex_reader.to_json(output)

    assert len(json_output) >= 1
    assert output.tokens is not None
    assert len(output.tokens) > 0


def test_non_standard_layout():
    """Test processing a project with non-standard layout where main.tex is in samples/ but resources are at root"""
    tex_reader = TexReader()

    # test working with non-standard layout
    # main.tex is in samples/ subdirectory, but main.bbl is at project root
    output = tex_reader.process(samples_dir_path + "/non_standard_layout")
    json_output = tex_reader.to_json(output)

    assert len(json_output) >= 1
    assert output.tokens is not None
    assert len(output.tokens) > 0

    # Verify project_root is set correctly
    assert output.project_root is not None
    assert output.project_root.name == "non_standard_layout"
    assert output.main_tex_path is not None
    assert output.main_tex_path.name == "main.tex"
    # Main tex is in samples/ subdirectory, project_root should be parent
    assert output.project_root == output.main_tex_path.parent.parent

    # Verify that bibliography was found and processed
    # The main.bbl file at the project root should be successfully resolved
    def find_in_tokens(tokens, check_fn):
        """Recursively search tokens using a check function"""
        if not isinstance(tokens, list):
            return False
        for token in tokens:
            if not isinstance(token, dict):
                continue
            if check_fn(token):
                return True
            if "content" in token and isinstance(token["content"], list):
                if find_in_tokens(token["content"], check_fn):
                    return True
        return False

    # Check bibliography
    bibliography_found = find_in_tokens(
        output.tokens, lambda t: t.get("type") == "bibliography"
    )
    assert bibliography_found, "Bibliography from main.bbl at project root should be found"

    # Check that input file from project root was loaded
    def has_intro_text(token):
        if token.get("type") == "text":
            content = token.get("content", "")
            return "introduction section loaded from inputs/intro.tex" in content
        return False

    input_found = find_in_tokens(output.tokens, has_intro_text)
    assert input_found, "Input file from inputs/intro.tex at project root should be found"
