import pytest
import os

from latex2json.tex_reader import TexReader


dir_path = os.path.dirname(os.path.abspath(__file__))
samples_dir_path = os.path.join(dir_path, "samples")


def test_tex_reader():
    tex_reader = TexReader()

    # test working on subfiles
    output = tex_reader.process(samples_dir_path + "/subfiles")
    json_output = tex_reader.to_json(output, merge_inline_tokens=False)

    assert len(json_output) >= 1
