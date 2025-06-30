import pytest
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.parser import Parser


def test_ignore_separator_patterns():
    parser = Parser()
    text = r"""
\hline
\vline
\hrulefill
\centerline
\cline{1}
\topsep
\parsep
\partopsep
\labelsep{1em}
\midrule[2pt]
\toprule[1pt]
\bottomrule[1pt]
\cmidrule(lr){1-2}
\hdashline[2pt]
\cdashline{1-2}
\specialrule{1pt}{2pt}{3pt}
\addlinespace[5pt]
\rule{1cm}{2cm}
\morecmidrules
\fboxsep{1pt}
\Xhline{2pt}
\tabcolsep
\colrule
\noalign
\endfirsthead
"""
    out = parser.parse(text)
    out = strip_whitespace_nodes(out)
    assert out == []


def test_ignore_name_patterns():
    parser = Parser()
    # make @ letter
    parser.parse(r"\makeatletter")

    text = r"""\Hy@org{https://example.com}"""
    out = parser.parse(text)
    assert out == []
