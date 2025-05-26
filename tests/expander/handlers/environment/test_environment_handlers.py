import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.types import (
    Token,
    TokenType,
    BEGIN_BRACE_TOKEN,
    END_BRACE_TOKEN,
    BEGIN_BRACKET_TOKEN,
    END_BRACKET_TOKEN,
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
    begin_token = Token(TokenType.ENVIRONMENT_START, env_name)
    end_token = Token(TokenType.ENVIRONMENT_END, env_name)

    if numbering:
        begin_token.numbering = numbering

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
    assert out[0] == Token(TokenType.ENVIRONMENT_START, "document")
    assert out[-1] == Token(TokenType.ENVIRONMENT_END, "document")

    # Test center environment
    out = expander.expand(r"\begin{center}Centered text\end{center}")
    assert out[0] == Token(TokenType.ENVIRONMENT_START, "center")
    assert out[-1] == Token(TokenType.ENVIRONMENT_END, "center")


def test_numbered_environments():
    expander = Expander()

    # Test equation environment (should be numbered)
    out = expander.expand(r"\begin{equation}1+1\end{equation}")
    assert out[0] == Token(TokenType.ENVIRONMENT_START, "equation", numbering="1")

    # Test equation* environment (should not be numbered)
    out = expander.expand(r"\begin{equation*}2+2\end{equation*}")
    assert out[0] == Token(TokenType.ENVIRONMENT_START, "equation*")


def test_environments_with_args():
    expander = Expander()

    # Test figure environment with optional placement argument
    out = expander.expand(r"\begin{figure}[htb]Content\end{figure}")
    assert out[0] == Token(TokenType.ENVIRONMENT_START, "figure")

    # Test tabular environment with required argument
    out = expander.expand(r"\begin{tabular}{|c|c|}Content\end{tabular}")
    assert out[0] == Token(TokenType.ENVIRONMENT_START, "tabular")


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
    assert out[0] == Token(TokenType.ENVIRONMENT_START, "figure")

    # Find center environment tokens
    center_start = None
    center_end = None
    for i, token in enumerate(out):
        if token.type == TokenType.ENVIRONMENT_START and token.value == "center":
            center_start = i
        elif token.type == TokenType.ENVIRONMENT_END and token.value == "center":
            center_end = i

    assert center_start is not None
    assert center_end is not None
    assert center_start < center_end


def test_math_environments():
    expander = Expander()

    # Test align environment
    out = expander.expand(r"\begin{align}x &= y\end{align}")
    assert out[0] == Token(TokenType.ENVIRONMENT_START, "align", numbering="1")

    # Test align* environment
    out = expander.expand(r"\begin{align*}x &= y\end{align*}")
    assert out[0] == Token(TokenType.ENVIRONMENT_START, "align*")


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
    expected = mock_env_token(expander, "equation", "1+1", numbering="1")
    assert_token_sequence(actual, expected)

    # # Test with multiple optional args
    # actual = expander.expand(r"\begin{env}[opt1][opt2]Content\end{env}")
    # expected = mock_env_token(expander, "env", "Content", opt_args=["opt1", "opt2"])
    # assert_token_sequence(actual, expected)

    # # Test with multiple required args
    # actual = expander.expand(r"\begin{env}{req1}{req2}Content\end{env}")
    # expected = mock_env_token(expander, "env", "Content", req_args=["req1", "req2"])
    # assert_token_sequence(actual, expected)
