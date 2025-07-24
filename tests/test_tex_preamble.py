import pytest
import os

from latex2json.tex_preamble import TexPreamble


dir_path = os.path.dirname(os.path.abspath(__file__))
samples_dir_path = os.path.join(dir_path, "samples")


def test_tex_preamble():

    text = r"""
\documentclass{article}

\newcommand{\aaa}{AAA}
\def\bea{\begin{eqnarray}}
\def\eea{\end{eqnarray}}

\usepackage{xcolor, tikz}
\usepackage[xxxx]{pgfplots}
\usetikzlibrary{arrows.meta}

\begin{document}
\end{document}
    """

    processor = TexPreamble()

    out = processor.get_preamble(text).strip()
    assert out.startswith(r"\newcommand{\aaa}")
    assert out.endswith(r"\usetikzlibrary{arrows.meta}")

    # test with file
    out = processor.get_preamble_from_file(samples_dir_path + "/main.tex").strip()
    assert out.startswith(r"\usepackage{package1}")
    assert out.endswith(r"\usepackage{package2}")
