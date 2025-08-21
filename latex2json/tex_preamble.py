import re
import sys, os
import logging

from latex2json.tex_file_extractor import BEGIN_DOCUMENT_PATTERN, DOCUMENTCLASS_PATTERN
from latex2json.utils.tex_utils import read_tex_file_content, strip_latex_comments

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TexPreamble:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def get_preamble(self, content: str) -> str:
        r"""Extract all content between \documentclass and \begin{document}"""

        content = strip_latex_comments(content)

        # get all content before begin document
        begin_doc_search = BEGIN_DOCUMENT_PATTERN.search(content)
        if begin_doc_search:
            content = content[: begin_doc_search.start()]

        # limit to documentclass onwards
        doc_class_match = DOCUMENTCLASS_PATTERN.search(content)
        if doc_class_match:
            content = content[doc_class_match.end() :]

        return content.strip()

    def get_preamble_from_file(self, file_path: str) -> str:
        try:
            content = read_tex_file_content(file_path, extension=".tex")
            return self.get_preamble(content)
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}", exc_info=True)
            return ""


if __name__ == "__main__":
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

    out = processor.get_preamble(text)
    print(out)

    # out = processor.get_preamble_from_file("papers/new/arXiv-2304.02643v1/segany.tex")
    # print(out)
