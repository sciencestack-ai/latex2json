import pytest
from latex2json.renderer.json.json_renderer import JSONRenderer


def test_json_output_of_math_n_text_equations():

    # first, check that equation adjacent commands and text are separated by a space at least
    text = r"""
    \def\one{one}
    $\frac\one$ % -> \frac one
    """.strip()
    renderer = JSONRenderer()
    json = renderer.parse(text)
    assert len(json) == 1
    # notice that the command and text are separated by a space
    assert json[0] == {"type": "equation", "content": r"\\frac one"}

    # test bigger case
    text = r"""
\begin{equation}
\begin{cases}
\fbox{$\frac12$} \text{$...$} % for math, we preserve the original latex format and ensure $$ are properly enclosed within box/text commands in equations
\end{cases}
\end{equation}
""".strip()

    json = renderer.parse(text)
    assert len(json) == 1
    assert json[0] == {
        "type": "equation",
        "display": "block",
        "name": "equation",
        "numbering": "1",
        "content": [
            {
                "type": "equation_array",
                "name": "cases",
                "content": [
                    {
                        "type": "row",
                        "content": [
                            [
                                {
                                    "type": "text",
                                    "content": r"\fbox{$\frac12$} \text{$...$}",
                                }
                            ]
                        ],
                    }
                ],
            }
        ],
    }
