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
