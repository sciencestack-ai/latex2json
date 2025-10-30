import pytest
import os

from latex2json.tex_reader import TexReader


dir_path = os.path.dirname(os.path.abspath(__file__))
samples_dir_path = os.path.join(dir_path, "samples")


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
