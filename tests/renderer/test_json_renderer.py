import pytest
from latex2json.nodes.node_types import NodeTypes
from latex2json.renderer.json.json_renderer import JSONRenderer


def test_json_output_of_math_n_text_equations():

    # first, check that equation adjacent commands and text are separated by a space at least
    text = r"""
    \def\one{one}
    $\chi\one$ % -> \chi one
    """.strip()
    renderer = JSONRenderer()
    json = renderer.parse(text)
    assert len(json) == 1
    # notice that the command and text are separated by a space
    assert json[0] == {"type": NodeTypes.EQUATION, "content": r"\chi one"}

    # test bigger case
    text = r"""
\begin{equation}
\begin{cases}
\ref{eq:1}\fbox{$\alpha12$} \text{$...$} % for math, we preserve the original latex format and ensure $$ are properly enclosed within box/text commands in equations
\end{cases}
\end{equation}
""".strip()

    json = renderer.parse(text)
    assert len(json) == 1
    assert json[0] == {
        "type": NodeTypes.EQUATION,
        "display": "block",
        "name": "equation",
        "numbering": "1",
        "content": [
            {
                "type": NodeTypes.EQUATION_ARRAY,
                "name": "cases",
                "content": [
                    {
                        "type": NodeTypes.ROW,
                        "content": [
                            [
                                {
                                    "type": NodeTypes.REF,
                                    "content": ["eq:1"],
                                },
                                {
                                    "type": NodeTypes.TEXT,
                                    "content": r"\fbox{$\alpha12$} \text{$...$}",
                                },
                            ]
                        ],
                    }
                ],
            }
        ],
    }


def test_json_output_of_captions():
    # check that caption numbering in nested environments is transferred to the parent float env
    text = r"""
    \begin{figure}  % json output is numbering = 1
    \begin{center}
    \caption{FIGURE} % numbering has been transferred to the figure output
    \end{center}
    \end{figure}
    """.strip()
    renderer = JSONRenderer()
    json = renderer.parse(text)
    assert len(json) == 1
    assert json[0]["type"] == NodeTypes.FIGURE
    assert json[0]["numbering"] == "1"


def test_output_excludes_tokens_after_document_env():
    text = r"""
    PRE DOC
    \begin{document}
    DOC
    \end{document}
    AFTER END DOC
    """.strip()
    renderer = JSONRenderer()
    json = renderer.parse(text)

    # only PRE DOC + document token output included, no AFTER END DOC
    assert len(json) == 2
    assert json[0]["type"] == NodeTypes.TEXT
    assert json[0]["content"].strip() == "PRE DOC"
    assert json[1]["type"] == NodeTypes.DOCUMENT
    # assert json[1]["name"] == NodeTypes.DOCUMENT


def test_json_output_of_begin_end_sections():
    # ensure that begin/end sections are properly nested
    text = r"""
    \begin{section}{Intro}\label{sec:intro}
    Section 1
    \begin{subsection}{Subsec 1}\label{subsec:1}
    Subsec 1
    \end{subsection}
    \end{section}

    Post Sec Intro

    \begin{section}{Sec 2}
    Section 2
    \end{section}

    Post Sec 2
    """.strip()
    renderer = JSONRenderer()
    json = renderer.parse(text)

    expected = [
        {
            "type": NodeTypes.ENVIRONMENT,
            "name": "section",
            "content": [
                {
                    "type": NodeTypes.SECTION,
                    "labels": ["sec:intro"],
                    "level": 1,
                    "numbering": "1",
                    "title": [{"type": "text", "content": "Intro"}],
                    "content": [
                        {"type": "text", "content": "Section 1 "},
                        {
                            "type": NodeTypes.ENVIRONMENT,
                            "name": "subsection",
                            "content": [
                                {
                                    "type": NodeTypes.SECTION,
                                    "labels": ["subsec:1"],
                                    "level": 2,
                                    "numbering": "1.1",
                                    "title": [{"type": "text", "content": "Subsec 1"}],
                                    "content": [
                                        {"type": "text", "content": "Subsec 1"}
                                    ],
                                }
                            ],
                        },
                    ],
                }
            ],
        },
        {"type": "text", "content": "Post Sec Intro\n"},
        {
            "type": NodeTypes.ENVIRONMENT,
            "name": "section",
            "content": [
                {
                    "type": NodeTypes.SECTION,
                    "level": 1,
                    "numbering": "2",
                    "title": [{"type": "text", "content": "Sec 2"}],
                    "content": [{"type": "text", "content": "Section 2"}],
                }
            ],
        },
        {"type": "text", "content": "Post Sec 2"},
    ]

    assert json == expected
