from typing import List, Optional
from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.expander.handlers.sectioning.test_section_handlers import mock_section_token


def mock_caption_token(
    expander: Expander,
    caption_text: str,
    opt_arg: Optional[str] = None,
    numbering: Optional[str] = None,
    counter_name: Optional[str] = None,
):
    out_tokens = mock_section_token(
        expander,
        "caption",
        caption_text,
        opt_arg,
        numbering=numbering,
        counter_name=counter_name,
    )
    return out_tokens


class DummyCaption:
    def __init__(
        self,
        caption_text: str,
        float_env: str,
        opt_arg: Optional[str] = None,
        numbering: Optional[str] = None,
    ):
        self.caption_text = caption_text
        self.float_env = float_env
        self.opt_arg = opt_arg
        self.numbering = numbering


def assert_caption_instances(expander: Expander, expected_captions: List[DummyCaption]):
    caption_index = 0
    while not expander.eof():
        tokens = expander.next_non_expandable_tokens()
        out = strip_whitespace_tokens(tokens)
        if out and out[0].value == "caption":
            if caption_index >= len(expected_captions):
                break

            exp = expected_captions[caption_index]
            float_env = expander.get_parent_float_env()
            assert float_env and float_env.name == exp.float_env
            mock_caption = mock_caption_token(
                expander,
                exp.caption_text,
                opt_arg=exp.opt_arg,
                numbering=exp.numbering,
            )
            assert expander.check_tokens_equal(out, mock_caption)
            caption_index += 1

    assert caption_index == len(expected_captions)


def test_caption_handler():
    expander = Expander()

    text = r"""
    \counterwithin{figure}{section}

    \section{SECTION}
    \begin{figure}[htb]
        \caption{FIGURE}
        \begin{subfigure}{sss}
            \caption{SUBFIGURE 2}
        \end{subfigure}
    \end{figure}

    \begin{table}[htb]
    \caption[SHORT]{TABLE}
    \end{table}

    \section{SECTION 2}
    \begin{figure}[htb] % reset counter
        \caption{FIGURE 2}
    \end{figure}

    % test with \caption*
    \begin{figure}
        \caption* [XXX] {FIGURE 3}
    \end{figure}

    \begin{figure*} % still numbered!
        \subcaption {FIGURE 4}
    \end{figure*}
    """
    expander.set_text(text)

    expected_captions = [
        DummyCaption(float_env="figure", numbering="1.1", caption_text="FIGURE"),
        DummyCaption(
            float_env="subfigure", numbering="1.1.a", caption_text="SUBFIGURE 2"
        ),
        DummyCaption(
            float_env="table",
            numbering="1",
            caption_text="TABLE",
            opt_arg="SHORT",
        ),
        DummyCaption(float_env="figure", numbering="2.1", caption_text="FIGURE 2"),
        DummyCaption(float_env="figure", caption_text="FIGURE 3", opt_arg="XXX"),
        DummyCaption(float_env="figure", caption_text="FIGURE 4", numbering="2.2"),
    ]

    assert_caption_instances(expander, expected_captions)


def test_figure_wrapfigure_captions():
    expander = Expander()

    text = r"""
    \begin{wrapfigure}{r}{0.5\textwidth}
    \caption{CAPTION}
    \end{wrapfigure}

    \begin{figure}[h]
    \caption{FIGURE}
    \end{figure}
    """
    expander.set_text(text)

    expected_captions = [
        DummyCaption(float_env="figure", numbering="1", caption_text="CAPTION"),
        DummyCaption(float_env="figure", numbering="2", caption_text="FIGURE"),
    ]

    assert_caption_instances(expander, expected_captions)


def test_captionof_handler():
    expander = Expander()

    text = r"""
    \begin{minipage}{0.5\textwidth}
    \captionof{figure}{CAPTION}
    \end{minipage}
    """.strip()

    expander.set_text(text)

    caption_index = 0
    while not expander.eof():
        tokens = expander.next_non_expandable_tokens()
        out = strip_whitespace_tokens(tokens)
        if out and out[0].value == "caption":
            assert out == mock_caption_token(
                expander,
                "CAPTION",
                opt_arg="Figure 1",
                numbering="1",
            )
            caption_index += 1
            break

    assert caption_index == 1

    assert expander.state.get_counter_value("figure") == 1


def test_nested_caption_numbering():
    expander = Expander()

    text = r"""
    \begin{table}
    \begin{spacing}
    \begin{center}
        \caption{TABLE} % ensure numbered even if nested deep inside table
    \end{center}
    \end{spacing}
    \end{table}
    """
    expander.set_text(text)

    expected_captions = [
        DummyCaption(float_env="table", numbering="1", caption_text="TABLE"),
    ]
    assert_caption_instances(expander, expected_captions)

    # test figure and table nested
    text = r"""
    \begin{figure}
    \begin{table}
        \caption{INNER TABLE}  % numbered as 2 (continuing 1 from above)
    \end{table}
    \caption{OUTER FIGURE} % numbered as 1 (figure)
    \end{figure}
    """
    expander.set_text(text)

    expected_captions = [
        DummyCaption(float_env="table", numbering="2", caption_text="INNER TABLE"),
        DummyCaption(float_env="figure", numbering="1", caption_text="OUTER FIGURE"),
    ]
    assert_caption_instances(expander, expected_captions)


def test_captionbox_handler():
    """Test captionbox command - transforms to caption + contents tokens."""
    expander = Expander()

    text = r"""
    \begin{figure}
        \captionbox{A cat}{\includegraphics{cat}}
    \end{figure}
    """
    expander.set_text(text)

    # After transformation, we should see: \caption{A cat} \includegraphics{cat}
    caption_found = False
    graphics_found = False

    while not expander.eof():
        tokens = expander.next_non_expandable_tokens()
        out = strip_whitespace_tokens(tokens)
        if out and out[0].value == "caption":
            # Check the caption token
            assert out[0].args
            caption_text = expander.convert_tokens_to_str(out[0].args[0])
            assert caption_text == "A cat"
            assert out[0].numbering == "1"
            caption_found = True
        elif out and out[0].value == "includegraphics":
            graphics_found = True

    assert caption_found and graphics_found
