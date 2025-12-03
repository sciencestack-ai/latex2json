from latex2json.expander.expander import Expander


def test_maketitle():

    expander = Expander()

    text = r"""
    \author{Yu Deng \xxx} % defer expansion until \maketitle
    \author{Second man} % \and is added between them
    \title{First title}
    \title{My title}

    \def\xxx{XXX}

    \maketitle
    """
    out = expander.expand(text)
    out = [t for t in out if t.value != "newline"]
    out_str = expander.convert_tokens_to_str(out).strip()

    # With new design, maketitle is wrapped in CommandWithArgsToken
    # Output should be: \maketitle{\title{My title}\author{Yu Deng XXX \and Second man}}
    assert out_str.startswith(r"\maketitle{")
    assert r"\title{My title}" in out_str
    assert r"\author{Yu Deng XXX \and Second man}" in out_str
    assert out_str.endswith("}")

    # Verify title is using the last one and \and is added between authors
    assert "First title" not in out_str, "Should use last title only"
    assert r"\and" in out_str, "Should have \\and between authors"


def test_maketitle_with_redefined_at_maketitle():
    r"""Test that redefined \@maketitle still preserves semantic info via \@title, \@author"""
    expander = Expander()

    text = r"""
    \def\xxx{PRE}

    \title{My Title \xxx}
    \author{John Doe}

    \def\xxx{POST}

    \makeatletter
    \def\@maketitle{%
        TITLE: \@title
        AUTHOR: \@author
    }
    \makeatother

    \maketitle
    """
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()

    # Should contain semantic tokens even inside redefined \@maketitle
    assert r"\title{My Title POST}" in out_str
    assert r"\author{John Doe}" in out_str


def test_maketitle_renewcommand_replaces():
    r"""
    Test that \renewcommand{\@title} correctly REPLACES the content.
    This is standard LaTeX behavior - user redefinitions should take effect.
    """
    expander = Expander()

    text = r"""
    \title{Original Title}
    \author{Original Author}

    \makeatletter
    % hardcode replacement of \@title and \@author
    \renewcommand{\@title}{REPLACED TITLE \xxx}
    \def\@author{REPLACED AUTHOR}
    \makeatother

    \def\xxx{XXX}

    \maketitle
    """
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()

    # User's \renewcommand should take effect (correct LaTeX behavior)
    assert r"\title{REPLACED TITLE XXX}" in out_str
    assert r"\author{REPLACED AUTHOR}" in out_str
    # Original content should NOT appear
    assert "Original Title" not in out_str
    assert "Original Author" not in out_str


def test_maketitle_redefinition_simple():
    expander = Expander()

    text = r"""
    \title{Original Title}
    \author{Original Author}

    \def\maketitle{FAKE}
    \maketitle
    """
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "FAKE"


def test_renewcommand_title_with_side_effects():
    r"""
    Test that \renewcommand{\title} can execute side effects like \newcommand
    while still populating frontmatter and preserving semantic wrapping.
    """
    expander = Expander()

    text = r"""
    \def\titlefont#1{FONT[#1]}
    \renewcommand{\title}[1]{\newcommand{\titlelist}{\titlefont{#1}}}

    \title{My Great Title}

    Result: \titlelist

    \maketitle
    """
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()

    # Side effect: \titlelist should be defined and work
    assert "Result: FONT[My Great Title]" in out_str

    # Frontmatter: \maketitle should still have content
    assert r"\maketitle{" in out_str
    assert r"\title{My Great Title}" in out_str
    assert expander.get_macro("titlelist")


def test_renewcommand_title_with_multiple_args():
    r"""Test \renewcommand{\title}[N] with multiple arguments stores all args"""
    expander = Expander()

    text = r"""
    \renewcommand{\title}[3]{\newcommand{\mytitle}{#1-#2-#3}}

    \title{A}{B}{C}

    Title is: \mytitle

    \maketitle
    """
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()

    # Side effect should work
    assert "Title is: A-B-C" in out_str

    # All args should be stored in frontmatter and appear in maketitle
    assert r"\maketitle{" in out_str
    assert r"\title{A}{B}{C}" in out_str
