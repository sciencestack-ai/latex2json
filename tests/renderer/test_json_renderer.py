import pytest
from latex2json.nodes.base_nodes import TextNode
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
    assert json[0] == {
        "type": NodeTypes.EQUATION,
        "content": [{"type": NodeTypes.TEXT, "content": r"\chi one"}],
    }

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

    # Exclude PRE DOC and AFTER END DOC
    assert len(json) == 1
    assert json[0]["type"] == NodeTypes.DOCUMENT

    # BUT test nested documents
    text = r"""
    \begin{document}
    \begin{document}
    DOC
    \end{document}
    AFTER INNER END DOC % not stripped! This is after all inside the document env
    \end{document}
    AFTER OUTER END DOC % this is stripped!
    """.strip()
    json = renderer.parse(text)
    assert len(json) == 1
    assert json[0]["type"] == NodeTypes.DOCUMENT
    doc_content = json[0]["content"]
    assert len(doc_content) == 2
    assert doc_content[0]["type"] == NodeTypes.DOCUMENT
    assert doc_content[1]["type"] == NodeTypes.TEXT
    assert doc_content[1]["content"].strip() == "AFTER INNER END DOC"
    # assert json[1]["type"] == NodeTypes.DOCUMENT
    # assert json[2]["type"] == NodeTypes.TEXT
    # assert json[2]["content"].strip() == "AFTER INNER END DOC"


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


def test_sanitize_equation_token():
    renderer = JSONRenderer()

    text = r"""
    $\ref{eq:1}$
    """.strip()
    json = renderer.parse(text)
    assert len(json) == 1
    assert json[0] == {"type": NodeTypes.REF, "content": ["eq:1"]}


def test_preserve_empty_align_cells():
    renderer = JSONRenderer()
    text = r"""
    \begin{align}
    P &= 33 \\ 
      &= 44
    \end{align}
    """.strip()
    json = renderer.parse(text)
    assert len(json) == 1
    assert json[0] == {
        "type": NodeTypes.EQUATION_ARRAY,
        "name": "align",
        "content": [
            {
                "type": NodeTypes.ROW,
                "numbering": "1",
                "content": [
                    [{"type": NodeTypes.TEXT, "content": "P"}],
                    [{"type": NodeTypes.TEXT, "content": "= 33"}],
                ],
            },
            {
                "type": NodeTypes.ROW,
                "numbering": "2",
                # empty cell is preserved
                "content": [[], [{"type": NodeTypes.TEXT, "content": "= 44"}]],
            },
        ],
    }


def test_tabular_with_empty_cells_and_colspan():
    """Test that empty cells and colspan are preserved in tabular output"""
    renderer = JSONRenderer()

    text = r"""
\begin{tabular}{l|rr|r}
    \toprule
          & \multicolumn{2}{c}{\% train examples with} & \multicolumn{1}{c}{\% valid with} \\
          & \multicolumn{1}{c}{dup in train} & \multicolumn{1}{c}{dup in valid} & \multicolumn{1}{c}{dup in train} \\
          \midrule
    C4    & 3.04\% & 1.59\% & 4.60\%  \\
    RealNews & 13.63\% & 1.25\% & 14.35\%  \\
    \bottomrule
    \end{tabular}
    """.strip()

    json = renderer.parse(text)
    assert len(json) == 1
    assert json[0]["type"] == NodeTypes.TABULAR
    assert json[0]["name"] == "tabular"

    content = json[0]["content"]

    # First row: empty cell, colspan=2 cell, regular cell
    assert content[0][0]["content"] == []  # Empty cell preserved
    assert content[0][1]["colspan"] == 2
    assert content[0][1]["content"] == [
        {"type": NodeTypes.TEXT, "content": "% train examples with"}
    ]
    assert content[0][2]["content"] == [
        {"type": NodeTypes.TEXT, "content": "% valid with"}
    ]

    # Second row: empty cell, three regular cells
    assert content[1][0]["content"] == []  # Empty cell preserved
    assert content[1][1]["content"] == [
        {"type": NodeTypes.TEXT, "content": "dup in train"}
    ]
    assert content[1][2]["content"] == [
        {"type": NodeTypes.TEXT, "content": "dup in valid"}
    ]
    assert content[1][3]["content"] == [
        {"type": NodeTypes.TEXT, "content": "dup in train"}
    ]

    # Third row: data cells
    assert content[2][0]["content"] == [{"type": NodeTypes.TEXT, "content": "C4"}]
    assert content[2][1]["content"] == [{"type": NodeTypes.TEXT, "content": "3.04%"}]
    assert content[2][2]["content"] == [{"type": NodeTypes.TEXT, "content": "1.59%"}]
    assert content[2][3]["content"] == [{"type": NodeTypes.TEXT, "content": "4.60%"}]

    # Fourth row: data cells
    assert content[3][0]["content"] == [{"type": NodeTypes.TEXT, "content": "RealNews"}]
    assert content[3][1]["content"] == [{"type": NodeTypes.TEXT, "content": "13.63%"}]
    assert content[3][2]["content"] == [{"type": NodeTypes.TEXT, "content": "1.25%"}]
    assert content[3][3]["content"] == [{"type": NodeTypes.TEXT, "content": "14.35%"}]


def test_bibliography_pruning():
    """Test that unused bibliography entries are pruned by default"""
    renderer = JSONRenderer()

    # Test with citations - should prune unused entries
    text = r"""
    \cite{key1, key2}

    \begin{thebibliography}{99}
    \bibitem{key1} Entry 1
    \bibitem{key2} Entry 2
    \bibitem{unused1} Unused 1
    \bibitem{unused2} Unused 2
    \end{thebibliography}
    """.strip()

    json = renderer.parse(text, organize_hierachy=False)

    # Find bibliography node (may have duplicates, just check first)
    bib_nodes = [node for node in json if node.get("type") == "bibliography"]
    assert len(bib_nodes) >= 1

    # Check that only cited entries are included
    bib_entries = bib_nodes[0]["content"]
    assert len(bib_entries) == 2
    assert bib_entries[0]["key"] == "key1"
    assert bib_entries[1]["key"] == "key2"

    # Test with \nocite{*} - should keep all entries
    text_with_nocite_all = r"""
    \cite{key1}
    \nocite{*}

    \begin{thebibliography}{99}
    \bibitem{key1} Entry 1
    \bibitem{key2} Entry 2
    \bibitem{key3} Entry 3
    \end{thebibliography}
    """.strip()

    renderer2 = JSONRenderer()
    json2 = renderer2.parse(text_with_nocite_all, organize_hierachy=False)
    bib_nodes2 = [node for node in json2 if node.get("type") == "bibliography"]
    bib_entries2 = bib_nodes2[0]["content"]
    assert len(bib_entries2) == 3  # All entries kept due to \nocite{*}

    # Test disabling pruning
    renderer3 = JSONRenderer(prune_bibliography=False)
    json3 = renderer3.parse(text, organize_hierachy=False)
    bib_nodes3 = [node for node in json3 if node.get("type") == "bibliography"]
    bib_entries3 = bib_nodes3[0]["content"]
    assert len(bib_entries3) == 4  # All entries kept when pruning disabled
