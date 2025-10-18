from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens


def test_ignore_formatting_handlers():
    expander = Expander()
    text = r"""
    \makeatletter
    
    \/
    \subjclass[xx]{Secondary 01A80}
    \FloatBarrier
    \stackMath
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

    \titlelabel{(\thesubsection)}
    \titleformat{\section}[hang]
{\normalfont\Large\bfseries}{\thesection}{1em}{}

    \titlespacing*{\paragraph}
    {0pt}{3.25ex plus 1ex minus .2ex}{1.5ex plus .2ex}

    \printcontents{}{1}{\setcounter{tocdepth}{2}}

    \setmathfont[range=\setminus, Scale=MatchUppercase]{Asana-Math.otf}
    \ExecuteBibliographyOptions{safeinputenc=true,backref=true,giveninits,useprefix=true,maxnames=5,doi=false,eprint=true,isbn=false,url=false}

    \setdefaultlanguage{english}
    \tracinglostchars=3
    \tracingpages 1

    \epsfxsize8truecm
    
    \tcbset{colback=pink!50!20, colframe=white, boxrule=0mm, sharp corners}
    \tcbuselibrary{skins}

    \renewbibmacro{in:}{}
    \stackMath

    \subjclass{Primary 01A80}
    \subjclass[xx]{Secondary 01A80}

    \hyphenchar\font45
    \skewchar\somefont='177

    \fontsize{.4\dimexpr(\f@size pt)}{0}

    \fancyhead[R]{Simple text}

    \errorcontextlines=10

    \mag=1000
    \magstep2
    
    \newsymbol\upharpoonright 1316

    \delimitershortfall=-2pt

    \Hy@MakeCurrentHref{\@currenvir.\the\Hy@linkcounter}
    \Hy@raisedlink{\hyper@anchorstart{\@currentHref}\hyper@anchorend}

    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out == []

    # test vrule and hrule
    out = expander.expand(r"\vrule height 2pt depth -1.6pt width 23pt")
    assert out == []

    out = expander.expand(r"\hrule width 23pt")
    assert out == []

    # test \\[0.5em] -> \\
    out = expander.expand(r"\\[0.5em] after")
    assert out == expander.expand(r"\\ after")

    # test \\[0.5em] -> \\
    out = expander.expand(r"\\   [0.5em] after")
    assert out == expander.expand(r"\\ after")

    # test rcsInfo
    out = expander.expand(
        r"\rcsInfo $Id: manuscript.tex,v 1792 2025/06/07 13:02:08 karplavi Exp karplavi $"
    )
    assert out == []


def test_ignore_separator_patterns():
    expander = Expander()
    text = r"""
    \hline
    \vline
    \hrulefill
    \centerline
    \cline{1}
    \topsep
    \parsep
    \partopsep
    \midrule[2pt]
    \toprule[2pt]
    \bottomrule[5pt]
    \cmidrule(lr){1-2}
    \hdashline[2pt]
    \cdashline{1-2}
    \specialrule{1pt}{2pt}{3pt}
    \addlinespace[5pt]
    \rule{1cm}{2cm}
    \morecmidrules
    \Xhline{2pt}
    \tabcolsep
    \colrule
    \noalign
    \endfirsthead
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out == []
