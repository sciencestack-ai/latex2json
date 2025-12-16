from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token


def test_etoolbox_patchcmds():
    expander = Expander()

    text = r"""
    \makeatletter

    \def\foo{foo}
    \patchcmd{\foo}{o}{ MIDDLE O }{success}{failure}

    \foo % foo -> f MIDDLE O o

    \pretocmd{\foo}{prepend }{success}{failure}
    \foo % f MIDDLE O o -> prepend f MIDDLE O o

    \apptocmd{\foo}{ append}{success}{failure}
    \foo % prepend f MIDDLE O o -> prepend f MIDDLE O o append
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == [
        "f MIDDLE O o",
        "prepend f MIDDLE O o",
        "prepend f MIDDLE O o append",
    ]


def test_etoolbox_toggles():
    expander = Expander()

    text = r"""
    \newtoggle{mytest}
    \iftoggle{mytest}{TRUE}{FALSE}

    \toggletrue{mytest}
    \iftoggle{mytest}{TRUE}{FALSE}

    \togglefalse{mytest}
    \iftoggle{mytest}{TRUE}{FALSE}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == ["FALSE", "TRUE", "FALSE"]


def test_etoolbox_toggles_nested():
    expander = Expander()

    text = r"""
    \newtoggle{outer}
    \newtoggle{inner}

    \toggletrue{outer}
    \togglefalse{inner}

    \iftoggle{outer}{
        OUTER-TRUE
        \iftoggle{inner}{INNER-TRUE}{INNER-FALSE}
    }{
        OUTER-FALSE
    }
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == ["OUTER-TRUE", "INNER-FALSE"]


def test_etoolbox_toggles_undefined():
    expander = Expander()

    # Test undefined toggle defaults to False
    text = r"""
    \iftoggle{undefined}{TRUE}{FALSE}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "FALSE"


def test_etoolbox_csappto_cspreto():
    expander = Expander()

    text = r"""
    \def\foo{middle}
    \csappto{foo}{ end}
    \foo

    \cspreto{foo}{start }
    \foo
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == ["middle end", "start middle end"]


def test_etoolbox_ifstrequal_basic():
    expander = Expander()

    text = r"""
    \ifstrequal{5}{5}{True!}{False!}
    \ifstrequal{5}{6}{True!}{False!}
    \ifstrequal{hello}{hello}{Match}{No match}
    \ifstrequal{hello}{world}{Match}{No match}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == ["True!", "False!", "Match", "No match"]

    text = r"""
    \ifstrequal{foo bar}{foo bar}{Equal}{Not equal}
    \ifstrequal{foo bar}{foobar}{Equal}{Not equal}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == ["Equal", "Not equal"]

    text = r"""
    \ifstrequal{}{}{Both empty}{Not equal}
    \ifstrequal{}{text}{Both empty}{Not equal}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == ["Both empty", "Not equal"]

    text = r"""
    \def\foo{test}
    \def\bar{test}
    \def\baz{other}
    \ifstrequal{\foo}{\bar}{Macros equal}{Macros not equal}
    \ifstrequal{\foo}{\baz}{Macros equal}{Macros not equal}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == ["Macros equal", "Macros not equal"]


def test_etoolbox_ifdef_basic():
    r"""Test \ifdef with defined and undefined commands."""
    expander = Expander()

    text = r"""
    \def\definedcmd{value}
    \ifdef{\definedcmd}{DEFINED}{UNDEFINED}
    \ifdef{\undefinedcmd}{DEFINED}{UNDEFINED}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == ["DEFINED", "UNDEFINED"]


def test_etoolbox_ifdef_with_relax():
    r"""Test \ifdef treats \relax as defined."""
    expander = Expander()

    text = r"""
    \let\relaxcmd\relax
    \ifdef{\relaxcmd}{DEFINED}{UNDEFINED}
    \ifdef{\relax}{DEFINED}{UNDEFINED}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == ["DEFINED", "DEFINED"]


def test_etoolbox_ifcsdef_basic():
    r"""Test \ifcsdef with control sequence names."""
    expander = Expander()

    text = r"""
    \def\definedcmd{value}
    \ifcsdef{definedcmd}{DEFINED}{UNDEFINED}
    \ifcsdef{undefinedcmd}{DEFINED}{UNDEFINED}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == ["DEFINED", "UNDEFINED"]


def test_etoolbox_ifcsdef_with_relax():
    r"""Test \ifcsdef treats \relax as defined."""
    expander = Expander()

    text = r"""
    \let\relaxcmd\relax
    \ifcsdef{relaxcmd}{DEFINED}{UNDEFINED}
    \ifcsdef{relax}{DEFINED}{UNDEFINED}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == ["DEFINED", "DEFINED"]


def test_etoolbox_ifundef_basic():
    r"""Test \ifundef with defined and undefined commands."""
    expander = Expander()

    text = r"""
    \def\definedcmd{value}
    \ifundef{\definedcmd}{UNDEFINED}{DEFINED}
    \ifundef{\undefinedcmd}{UNDEFINED}{DEFINED}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == ["DEFINED", "UNDEFINED"]


def test_etoolbox_ifundef_with_relax():
    r"""Test \ifundef treats \relax as undefined."""
    expander = Expander()

    text = r"""
    \let\relaxcmd\relax
    \ifundef{\relaxcmd}{UNDEFINED}{DEFINED}
    \ifundef{\relax}{UNDEFINED}{DEFINED}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    # Both should be UNDEFINED because \relax is treated as undefined by \ifundef
    assert out_strs == ["UNDEFINED", "UNDEFINED"]


def test_etoolbox_ifcsundef_basic():
    r"""Test \ifcsundef with control sequence names."""
    expander = Expander()

    text = r"""
    \def\definedcmd{value}
    \ifcsundef{definedcmd}{UNDEFINED}{DEFINED}
    \ifcsundef{undefinedcmd}{UNDEFINED}{DEFINED}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == ["DEFINED", "UNDEFINED"]


def test_etoolbox_ifcsundef_with_relax():
    r"""Test \ifcsundef treats \relax as undefined."""
    expander = Expander()

    text = r"""
    \let\relaxcmd\relax
    \ifcsundef{relaxcmd}{UNDEFINED}{DEFINED}
    \ifcsundef{relax}{UNDEFINED}{DEFINED}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    # Both should be UNDEFINED because \relax is treated as undefined by \ifcsundef
    assert out_strs == ["UNDEFINED", "UNDEFINED"]


def test_etoolbox_ifdef_vs_ifundef():
    r"""Test the difference between \ifdef and \ifundef with \relax."""
    expander = Expander()

    text = r"""
    \def\normalcmd{value}
    \let\relaxcmd\relax

    \ifdef{\normalcmd}{DEF}{UNDEF}
    \ifundef{\normalcmd}{UNDEF}{DEF}

    \ifdef{\relaxcmd}{DEF}{UNDEF}
    \ifundef{\relaxcmd}{UNDEF}{DEF}

    \ifdef{\undefinedcmd}{DEF}{UNDEF}
    \ifundef{\undefinedcmd}{UNDEF}{DEF}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    # normalcmd: defined for both
    # relaxcmd: defined for ifdef, undefined for ifundef
    # undefinedcmd: undefined for both
    assert out_strs == ["DEF", "DEF", "DEF", "UNDEF", "UNDEF", "UNDEF"]


def test_etoolbox_ifcsdef_vs_ifcsundef():
    r"""Test the difference between \ifcsdef and \ifcsundef with \relax."""
    expander = Expander()

    text = r"""
    \def\normalcmd{value}
    \let\relaxcmd\relax

    \ifcsdef{normalcmd}{DEF}{UNDEF}
    \ifcsundef{normalcmd}{UNDEF}{DEF}

    \ifcsdef{relaxcmd}{DEF}{UNDEF}
    \ifcsundef{relaxcmd}{UNDEF}{DEF}

    \ifcsdef{undefinedcmd}{DEF}{UNDEF}
    \ifcsundef{undefinedcmd}{UNDEF}{DEF}
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    # normalcmd: defined for both
    # relaxcmd: defined for ifcsdef, undefined for ifcsundef
    # undefinedcmd: undefined for both
    assert out_strs == ["DEF", "DEF", "DEF", "UNDEF", "UNDEF", "UNDEF"]


def test_etoolbox_ifdef_nested():
    r"""Test nested \ifdef conditionals."""
    expander = Expander()

    text = r"""
    \def\outer{value}
    \def\inner{value}

    \ifdef{\outer}{
        OUTER-TRUE
        \ifdef{\inner}{INNER-TRUE}{INNER-FALSE}
    }{
        OUTER-FALSE
    }
    """.strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_strs = [s.strip() for s in out_str.split("\n") if s.strip()]
    assert out_strs == ["OUTER-TRUE", "INNER-TRUE"]
