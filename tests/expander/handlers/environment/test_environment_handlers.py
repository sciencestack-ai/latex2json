import pytest
from latex2json.expander.expander import Expander
from latex2json.expander.state import ProcessingMode
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import (
    EnvironmentStartToken,
    Token,
    TokenType,
    BEGIN_BRACE_TOKEN,
    END_BRACE_TOKEN,
    BEGIN_BRACKET_TOKEN,
    END_BRACKET_TOKEN,
    EnvironmentType,
)
from tests.test_utils import assert_token_sequence
from typing import List, Optional


def mock_env_token(
    expander: Expander,
    env_name: str,
    content: str,
    opt_args: List[str] = [],
    req_args: List[str] = [],
    numbering: Optional[str] = None,
    env_type: EnvironmentType = EnvironmentType.DEFAULT,
    display_name: Optional[str] = None,
):
    """Create a mock environment token sequence with optional arguments and numbering.

    Args:
        expander: The Expander instance
        env_name: Name of the environment
        content: Content inside the environment
        opt_arg: Optional argument in square brackets
        req_arg: Required argument in curly braces
        numbering: Optional numbering for the environment
    """
    begin_token = EnvironmentStartToken(
        env_name,
        numbering=numbering,
        env_type=env_type,
        display_name=display_name,
    )
    end_token = Token(TokenType.ENVIRONMENT_END, env_name)

    out_tokens = [begin_token]

    # Add optional arguments if provided
    for opt_arg in opt_args:
        out_tokens.extend(
            [BEGIN_BRACKET_TOKEN] + expander.expand(opt_arg) + [END_BRACKET_TOKEN]
        )

    # Add required arguments if provided
    for req_arg in req_args:
        out_tokens.extend(
            [BEGIN_BRACE_TOKEN] + expander.expand(req_arg) + [END_BRACE_TOKEN]
        )

    # Add main content
    out_tokens.extend(expander.expand(content))

    out_tokens.append(end_token)
    return out_tokens


def test_basic_environments():
    expander = Expander()

    # Test basic document environment
    out = expander.expand(r"\begin{document}Hello\end{document}")
    assert out[0] == EnvironmentStartToken("document")
    assert out[-1] == Token(TokenType.ENVIRONMENT_END, "document")

    # Test center environment
    out = expander.expand(r"\begin{center}Centered text\end{center}")
    assert out[0] == EnvironmentStartToken("center")
    assert out[-1] == Token(TokenType.ENVIRONMENT_END, "center")


def test_environments_with_alt_names():
    expander = Expander()

    # check wrapfigure -> figure

    out = expander.expand(
        r"\begin{wrapfigure}{r}{0.5\textwidth}Content\end{wrapfigure}"
    )
    assert out[0] == EnvironmentStartToken("figure")
    assert out[-1] == Token(TokenType.ENVIRONMENT_END, "figure")


def test_environments_with_args():
    expander = Expander()

    # Test figure environment with optional placement argument
    out = expander.expand(r"\begin{figure}[htb]Content\end{figure}")
    assert out[0] == EnvironmentStartToken("figure")

    # Test tabular environment with required argument
    out = expander.expand(r"\begin{tabular}{|c|c|}Content\end{tabular}")
    assert out[0] == EnvironmentStartToken("tabular")


def test_nested_environments():
    expander = Expander()

    text = r"""
    \begin{figure}[h]
        \begin{center}
            Content
        \end{center}
        \caption{A figure}
    \end{figure}
    """.strip()
    out = expander.expand(text)

    # Check outer environment
    assert out[0] == EnvironmentStartToken("figure")

    # Find center environment tokens
    center_start = None
    center_end = None
    for i, token in enumerate(out):
        if token == EnvironmentStartToken("center"):
            center_start = i
        elif token.type == TokenType.ENVIRONMENT_END and token.value == "center":
            center_end = i

    assert center_start is not None
    assert center_end is not None
    assert center_start < center_end


def test_math_environments_numbers():
    expander = Expander()

    # Test equation environment (should be numbered)
    out = expander.expand(r"\begin{equation}1+1\end{equation}")
    assert out[0] == EnvironmentStartToken(
        "equation", numbering="1", env_type=EnvironmentType.EQUATION
    )

    # Test equation* environment (should not be numbered)
    out = expander.expand(r"\begin{equation*}2+2\end{equation*}")
    assert out[0] == EnvironmentStartToken(
        "equation*", env_type=EnvironmentType.EQUATION
    )

    # But equation* with \tag should be numbered/tagged
    out = expander.expand(r"\begin{equation*}2+2\tag{eq22}\end{equation*}")
    assert out[0] == EnvironmentStartToken(
        "equation*", numbering="eq22", env_type=EnvironmentType.EQUATION
    )

    # also \[ \] with \tag should be numbered/tagged
    out = expander.expand(r"\[2+2\tag{xxx}\]")
    assert out[0] == EnvironmentStartToken(
        "equation*", numbering="xxx", env_type=EnvironmentType.EQUATION
    )


def test_mock_env_token():
    expander = Expander()

    # Test basic environment
    actual = expander.expand(r"\begin{document}Hello\end{document}")
    expected = mock_env_token(expander, "document", "Hello")
    assert_token_sequence(actual, expected)

    # Test with optional argument
    actual = expander.expand(r"\begin{figure}[htb]Content\end{figure}")
    expected = mock_env_token(expander, "figure", "Content")
    assert_token_sequence(actual, expected)

    # Test with required argument
    actual = expander.expand(r"\begin{tabular}{|c|c|}Content\end{tabular}")
    expected = mock_env_token(expander, "tabular", "Content")
    assert_token_sequence(actual, expected)

    # Test with numbering
    actual = expander.expand(r"\begin{equation}1+1\end{equation}")
    expected = mock_env_token(
        expander, "equation", "1+1", numbering="1", env_type=EnvironmentType.EQUATION
    )
    assert_token_sequence(actual, expected)

    # # Test with multiple optional args
    # actual = expander.expand(r"\begin{env}[opt1][opt2]Content\end{env}")
    # expected = mock_env_token(expander, "env", "Content", opt_args=["opt1", "opt2"])
    # assert_token_sequence(actual, expected)

    # # Test with multiple required args
    # actual = expander.expand(r"\begin{env}{req1}{req2}Content\end{env}")
    # expected = mock_env_token(expander, "env", "Content", req_args=["req1", "req2"])
    # assert_token_sequence(actual, expected)


def test_equation_environments():
    expander = Expander()

    # test that equation with \nonumber is not numbered
    text = r"""
    \begin{equation} \nonumber
    1+1 
    \end{equation}
""".strip()
    out = expander.expand(text)
    assert out[0] == EnvironmentStartToken(
        "equation", numbering=None, env_type=EnvironmentType.EQUATION
    )

    # test with normal \nonumber
    text = r"""
    \begin{equation}
    1+1 
    \end{equation}
""".strip()
    out = expander.expand(text)
    assert out[0] == EnvironmentStartToken(
        "equation", numbering="1", env_type=EnvironmentType.EQUATION
    )


def test_floatname():
    expander = Expander()

    # change env displayname
    expander.expand(r"\floatname{figure}{Fig.}")

    fig = expander.expand(r"\begin{figure}[h]\end{figure}")
    assert fig == mock_env_token(
        expander,
        "figure",
        content="",
        display_name="Fig.",
        env_type=EnvironmentType.DEFAULT,
    )


def test_verbatim_environments():
    expander = Expander()

    verbatim_env_tokens = expander.expand(
        r"\begin{verbatim}\newcommand{test}{123}\end {fake}##1\end{verbatim}"
    )
    assert verbatim_env_tokens[0] == EnvironmentStartToken(
        "verbatim", env_type=EnvironmentType.VERBATIM
    )
    # check that newcommand remains there unexpanded since this is a verbatim environment
    assert verbatim_env_tokens[1] == Token(TokenType.CONTROL_SEQUENCE, "newcommand")

    # check that parameter token is not collapsed to #1
    assert expander.check_tokens_equal(
        verbatim_env_tokens[-4:-1], expander.convert_str_to_tokens("##1")
    )
    assert verbatim_env_tokens[-1] == Token(TokenType.ENVIRONMENT_END, "verbatim")


def test_subequations_and_align():
    expander = Expander()

    text = r"""
    \def\fracc{\frac}
    \begin{subequations}
    \begin{align}
    a &= b \fracc{1}{2} \label{eq:1} \\ % eq number 1.a
    1+1  \\ % eq number 1.b
    c &= d \nonumber % no number!
    \end{align} 
    \begin{equation} % eq number 1.c
    2+2=4 
    \end{equation}
    \begin{align*} 
    aaa                % no number!
    \end{align*}
    \end{subequations}

    \begin{equation} % eq number 2
    55
    \label{eq:2}
    \end{equation}

    \begin{align}
    a &= b \\ % eq number 3
    c &= d % eq number 4
    \end{align}

    \begin{subequations}
    \begin{equation} % eq number 5.a
    1+1
    \end{equation}
    \end{subequations}

    % empty subequations also increment
    \begin{subequations} % theoretically number 6, but no equations inside to number
    \end{subequations}

    \begin{align} 
    \begin{matrix}  % these 2 matrix blocks are together as one equation (number 7), since there is no \\ split between them
    a & b \\
        c & d
    \end{matrix}
    \begin{pmatrix}
    a & b \\
        c & d
    \end{pmatrix}
    \end{align}
    """

    def assert_env_sequence(out: List[Token], expected_env_token_sequence: List[Token]):
        i = 0
        for tok in out:
            if tok == expected_env_token_sequence[i]:
                i += 1
                if i >= len(expected_env_token_sequence):
                    break

        assert i == len(expected_env_token_sequence)

    expected_env_token_sequence = [
        EnvironmentStartToken("subequations"),
        # \begin{align}
        EnvironmentStartToken("align", env_type=EnvironmentType.EQUATION_ALIGN),
        # equations inside align are numbered. Inside subequations, they are numbered as 1.a, 1.b, etc
        EnvironmentStartToken(
            "equation", numbering="1.a", env_type=EnvironmentType.EQUATION
        ),
        Token(TokenType.ENVIRONMENT_END, "equation"),
        EnvironmentStartToken(
            "equation", numbering="1.b", env_type=EnvironmentType.EQUATION
        ),
        Token(TokenType.ENVIRONMENT_END, "equation"),
        EnvironmentStartToken(
            "equation", env_type=EnvironmentType.EQUATION
        ),  # \nonumber means not numbered
        Token(TokenType.ENVIRONMENT_END, "equation"),
        # \end{align}
        Token(TokenType.ENVIRONMENT_END, "align"),
        # \begin{equation}
        EnvironmentStartToken(
            "equation", numbering="1.c", env_type=EnvironmentType.EQUATION
        ),
        Token(TokenType.ENVIRONMENT_END, "equation"),
        # \begin{align*}. all equations inside align* are not numbered
        EnvironmentStartToken("align*", env_type=EnvironmentType.EQUATION_ALIGN),
        EnvironmentStartToken("equation", env_type=EnvironmentType.EQUATION),
        Token(TokenType.ENVIRONMENT_END, "equation"),
        # \end{align*}
        Token(TokenType.ENVIRONMENT_END, "align*"),
        # \end{subequations}
        Token(TokenType.ENVIRONMENT_END, "subequations"),
        # \begin{equation}
        EnvironmentStartToken(
            "equation", numbering="2", env_type=EnvironmentType.EQUATION
        ),
        Token(TokenType.ENVIRONMENT_END, "equation"),
        # \begin{align}
        EnvironmentStartToken("align", env_type=EnvironmentType.EQUATION_ALIGN),
        EnvironmentStartToken(
            "equation", numbering="3", env_type=EnvironmentType.EQUATION
        ),
        Token(TokenType.ENVIRONMENT_END, "equation"),
        EnvironmentStartToken(
            "equation", numbering="4", env_type=EnvironmentType.EQUATION
        ),
        Token(TokenType.ENVIRONMENT_END, "equation"),
        Token(TokenType.ENVIRONMENT_END, "align"),
        # \begin{subequations}
        EnvironmentStartToken("subequations"),
        EnvironmentStartToken(
            "equation", numbering="5.a", env_type=EnvironmentType.EQUATION
        ),
        Token(TokenType.ENVIRONMENT_END, "equation"),
        Token(TokenType.ENVIRONMENT_END, "subequations"),
        # \begin{align}
        EnvironmentStartToken("align", env_type=EnvironmentType.EQUATION_ALIGN),
        EnvironmentStartToken(
            "equation", env_type=EnvironmentType.EQUATION, numbering="7"
        ),
        # \begin{matrix}
        EnvironmentStartToken(
            "matrix", env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY
        ),
        Token(TokenType.ENVIRONMENT_END, "matrix"),
        EnvironmentStartToken(
            "pmatrix", env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY
        ),
        Token(TokenType.ENVIRONMENT_END, "pmatrix"),
        Token(TokenType.ENVIRONMENT_END, "equation"),
        # \end{align}
        Token(TokenType.ENVIRONMENT_END, "align"),
    ]
    assert_env_sequence(expander.expand(text), expected_env_token_sequence)

    # now check \\ between matrix blocks are split inside align

    text = r"""
    \begin{align}
    \begin{matrix}  % number 8
    a & b \\
        c & d
    \end{matrix}
    \\ \nonumber
    \begin{pmatrix} % no number!
    a & b \\
        c & d
    \end{pmatrix}
    \\ 
    1 & 2  %  number 9
    \end{align}
    """
    expected_env_token_sequence = [
        # \begin{align}
        EnvironmentStartToken("align", env_type=EnvironmentType.EQUATION_ALIGN),
        EnvironmentStartToken(
            "equation", env_type=EnvironmentType.EQUATION, numbering="8"
        ),
        # \begin{matrix}
        EnvironmentStartToken(
            "matrix", env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY
        ),
        Token(TokenType.ENVIRONMENT_END, "matrix"),
        Token(TokenType.ENVIRONMENT_END, "equation"),
        # \begin{pmatrix}
        EnvironmentStartToken("equation", env_type=EnvironmentType.EQUATION),
        EnvironmentStartToken(
            "pmatrix", env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY
        ),
        Token(TokenType.ENVIRONMENT_END, "pmatrix"),
        Token(TokenType.ENVIRONMENT_END, "equation"),
        EnvironmentStartToken(
            "equation", env_type=EnvironmentType.EQUATION, numbering="9"
        ),
        Token(TokenType.ENVIRONMENT_END, "equation"),
        # \end{align}
        Token(TokenType.ENVIRONMENT_END, "align"),
    ]
    out = expander.expand(text)
    assert_env_sequence(out, expected_env_token_sequence)

    # but also check that \\ inside {...} are not split prematurely
    text = r"""
\begin{align}
\substack{ 11 \\ 22 } % \\ inside {...} is preserved, not split!
\end{align}
""".strip()
    out = expander.expand(text)

    expected_env_token_sequence = [
        # \begin{align}
        EnvironmentStartToken("align", env_type=EnvironmentType.EQUATION_ALIGN),
        EnvironmentStartToken(
            "equation", env_type=EnvironmentType.EQUATION, numbering="10"
        ),
        Token(TokenType.ENVIRONMENT_END, "equation"),
        Token(TokenType.ENVIRONMENT_END, "align"),
    ]
    assert_env_sequence(out, expected_env_token_sequence)

    # check that \\ inside {...} are not split prematurely
    out_str = expander.convert_tokens_to_str(out)
    assert r"\substack{ 11 \\ 22 }" in out_str
