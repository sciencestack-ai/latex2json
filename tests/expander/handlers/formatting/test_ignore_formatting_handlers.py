from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens


def test_ignore_formatting_handlers():
    expander = Expander()
    text = r"""
    \/
    \subjclass[xx]{Secondary 01A80}
    \FloatBarrier
    \stackMath
    \penalty1000
    \clubpenalty=0 
    \widowpenalty=0
    \kern.4ex

    \newmdenv[
        font=\ttfamily\small,
        linewidth=0.5pt,
        innerleftmargin=10pt,
        innerrightmargin=10pt,
        innertopmargin=10pt,
        innerbottommargin=10pt,
    ]{monobox}

    \titlecontents{section}
    [0em]
    {\vspace{0.4em}}
    {\contentslabel{2em}}
    {\bfseries}
    {\bfseries\titlerule*[0.5pc]{$\cdot$}\contentspage}
    [0.2em]

    \printcontents{}{1}{\setcounter{tocdepth}{2}}

    \setmathfont[range=\setminus, Scale=MatchUppercase]{Asana-Math.otf}
    \ExecuteBibliographyOptions{safeinputenc=true,backref=true,giveninits,useprefix=true,maxnames=5,doi=false,eprint=true,isbn=false,url=false}

    \setdefaultlanguage{english}
    \tracinglostchars=3

    
    \tcbset{colback=pink!50!20, colframe=white, boxrule=0mm, sharp corners}
    \tcbuselibrary{skins}

    \renewbibmacro{in:}{}
    \stackMath

    \penalty1000
    \clubpenalty=0 
    \widowpenalty=0
    \interfootnotelinepenalty=1000
    \subjclass{Primary 01A80}
    \subjclass[xx]{Secondary 01A80}
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out == []


def test_column_handlers():
    expander = Expander()
    text = r"""
    \twocolumn[Stuff]
    \onecolumn
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out == expander.expand("Stuff")


def test_texorpdfstring_handler():
    expander = Expander()
    text = r"\texorpdfstring{pdf version}{text version}"
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out == expander.expand("text version")
