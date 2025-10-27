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

    # check that title is using the last one, and is the first thing in the string
    expected_strs = [r"\title{My title}", r"\author{Yu Deng XXX \and Second man}"]

    check_str = out_str
    for expected_str in expected_strs:
        assert check_str.startswith(expected_str)
        check_str = check_str.replace(expected_str, "")
        check_str = check_str.strip()

    assert not check_str


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
