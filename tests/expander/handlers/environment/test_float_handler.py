from latex2json.expander.expander import Expander
from latex2json.tokens.types import EnvironmentStartToken, Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens


def test_float_handler():
    expander = Expander()
    # test these are converted to envstart + env end tokens
    text = r"""
\makeatletter
\@float{figure}[htb]
    \caption{FIGURE}
\end@float
\makeatother
""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out[0] == EnvironmentStartToken("figure")
    assert out[-1] == Token(type=TokenType.ENVIRONMENT_END, value="figure")

    # Verify that @float properly parses arguments using wrapfigure (3 args)
    text2 = r"""
\makeatletter
\@float{wrapfigure}[10]{r}{0.5\textwidth}
CONTENT HERE
\end@float
\makeatother
""".strip()
    out2 = expander.expand(text2)
    out2 = strip_whitespace_tokens(out2)

    # The environment should start with wrapfigure token
    env_start = out2[0]
    assert isinstance(env_start, EnvironmentStartToken)
    assert env_start.name == "figure"  # wrapfigure maps to "figure"

    # Verify args were parsed and consumed - content should not contain the literal arguments
    # Find CHARACTER tokens to reconstruct content
    content_chars = []
    for tok in out2:
        if tok.type == TokenType.CHARACTER:
            content_chars.append(tok.value)

    # The content should be "CONTENTHERE" (whitespace stripped), not include "r" or "0.5" etc
    content_str = "".join(content_chars)
    assert "CONTENT" in content_str, f"Content should be present"
    assert (
        "0.5" not in content_str
    ), f"Args like '0.5' should be consumed, got: {content_str}"
    assert content_str.replace(" ", "").startswith(
        "CONTENTHERE"
    ), f"Args should be consumed, got: {content_str}"


def test_newenvironment_float():
    expander = Expander()
    # test float env nested inside its own renewenvironment env (ensure no infinite recursion)
    text = r"""
\makeatletter
\renewenvironment{myenv}
  {\@float{myenv}}
  {\end@float}
\makeatother

\begin{myenv}TABLE\end{myenv}
""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out[0] == EnvironmentStartToken("myenv")
    assert out[-1] == Token(type=TokenType.ENVIRONMENT_END, value="myenv")


def test_dblfloat_handler():
    """Test @dblfloat and end@dblfloat handlers."""
    expander = Expander()

    # Basic @dblfloat test
    text = r"""
\makeatletter
\@dblfloat{table}
    \caption{DOUBLE TABLE}
\end@dblfloat
\makeatother
""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out[0] == EnvironmentStartToken("table")
    assert out[-1] == Token(type=TokenType.ENVIRONMENT_END, value="table")


def test_nested_float_and_dblfloat():
    """Test nested @float and @dblfloat with SAME env name to ensure proper delimiter matching."""
    expander = Expander()

    # Nested @float{table} inside @dblfloat{table} - SAME ENV NAME!
    # This is the critical test: delimiter matching must distinguish between
    # @float and @dblfloat even when they wrap the same environment name
    text = r"""
\makeatletter
\@dblfloat{table}
    Outer table content
    \@float{table}
        Inner table content
    \end@float
    More outer content
\end@dblfloat
\makeatother
""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)

    # Should have: table start (dblfloat), table start (float), table end (float), table end (dblfloat)
    # All have env_name="table" but different opening tokens!
    assert out[0] == EnvironmentStartToken("table")
    assert out[0].value == "table"

    # Find all table tokens - there should be 2 starts and 2 ends
    table_tokens = []
    for i, tok in enumerate(out):
        if isinstance(tok, EnvironmentStartToken) and tok.value == "table":
            table_tokens.append((i, "start"))
        elif tok.type == TokenType.ENVIRONMENT_END and tok.value == "table":
            table_tokens.append((i, "end"))

    assert (
        len(table_tokens) == 4
    ), f"Should have 2 table starts and 2 table ends, got {len(table_tokens)}"

    # Verify proper nesting: start, start, end, end
    assert table_tokens[0][1] == "start", "First should be outer table start"
    assert table_tokens[1][1] == "start", "Second should be inner table start"
    assert table_tokens[2][1] == "end", "Third should be inner table end"
    assert table_tokens[3][1] == "end", "Fourth should be outer table end"

    # Verify ordering
    assert (
        table_tokens[0][0]
        < table_tokens[1][0]
        < table_tokens[2][0]
        < table_tokens[3][0]
    ), "Proper nesting order"


def test_multiple_dblfloats():
    """Test multiple @dblfloat environments in sequence."""
    expander = Expander()

    text = r"""
\makeatletter
\@dblfloat{table}
    First table
\end@dblfloat
\@dblfloat{figure}
    First figure
\end@dblfloat
\makeatother
""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)

    # Find all environment tokens
    env_tokens = [
        tok
        for tok in out
        if isinstance(tok, EnvironmentStartToken)
        or tok.type == TokenType.ENVIRONMENT_END
    ]

    assert len(env_tokens) == 4  # 2 starts + 2 ends
    assert env_tokens[0] == EnvironmentStartToken("table")
    assert (
        env_tokens[1].value == "table"
        and env_tokens[1].type == TokenType.ENVIRONMENT_END
    )
    assert env_tokens[2] == EnvironmentStartToken("figure")
    assert (
        env_tokens[3].value == "figure"
        and env_tokens[3].type == TokenType.ENVIRONMENT_END
    )


def test_mismatched_float_dblfloat_delimiters():
    """Test that mismatched delimiters are handled (warnings logged, but graceful)."""
    expander = Expander()

    # @dblfloat with end@float - should log warning
    text = r"""
\makeatletter
\@dblfloat{table}
    Content
\end@float
\makeatother
""".strip()

    # Should not crash, just log warning
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)

    # The @dblfloat table should still be on the stack (not popped)
    # and end@float shouldn't find a matching @float
    assert out[0] == EnvironmentStartToken("table")

    # Test reverse: @float with end@dblfloat - should also log warning
    expander2 = Expander()
    text2 = r"""
\makeatletter
\@float{figure}
    Content
\end@dblfloat
\makeatother
""".strip()

    # Should not crash, just log warning
    out2 = expander2.expand(text2)
    out2 = strip_whitespace_tokens(out2)

    # The @float figure should still be on the stack (not popped)
    # and end@dblfloat shouldn't find a matching @dblfloat
    assert out2[0] == EnvironmentStartToken("figure")
