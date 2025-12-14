from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token


def test_keyval():
    expander = Expander()

    text = r"""
\def\xxx{XXX}
\makeatletter
\define@key{my}{foo}{Foo is #1 }
\define@key{my}{bar}[99]{Bar is #1 }
\define@key{my}{zac}{Zac is #1 }
\setkeys{my}{foo=\xxx,bar,zac=}

"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == r"Foo is XXX Bar is 99 Zac is"

    # test with commas inside braces
    text = r"""
    \setkeys{my}{
        foo={FOO,MAN},
        bar={BAR,MAN}
    }
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == r"Foo is FOO,MAN Bar is BAR,MAN"


def test_boolkey():
    expander = Expander()

    text = r"""
\makeatletter
\define@boolkey{opt}{mykey}[true]{Key was set to #1}
\setkeys{opt}{mykey=true}
\ifKV@opt@mykey TRUE\else FALSE\fi
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert "Key was set to true" in out_str
    assert "TRUE" in out_str

    # Test setting to false
    text = r"""
\makeatletter
\define@boolkey{opt}{mykey}[true]{Key was set to #1}
\setkeys{opt}{mykey=false}
\ifKV@opt@mykey TRUE\else FALSE\fi
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert "Key was set to false" in out_str
    assert "FALSE" in out_str

    # Test with custom prefix
    text = r"""
\makeatletter
\define@boolkey{opt}[ACM@]{natbib}[true]{Natbib: #1}
\setkeys{opt}{natbib}
\ifACM@natbib NATBIB-ON\else NATBIB-OFF\fi
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert "Natbib: true" in out_str
    assert "NATBIB-ON" in out_str

    # Test with custom prefix set to false
    text = r"""
\makeatletter
\define@boolkey{opt}[ACM@]{natbib}[true]{Natbib: #1}
\setkeys{opt}{natbib=false}
\ifACM@natbib NATBIB-ON\else NATBIB-OFF\fi
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert "Natbib: false" in out_str
    assert "NATBIB-OFF" in out_str

    # Test the + variant (allows \par in function body)
    text = r"""
\makeatletter
\define@boolkey+{opt}[PREFIX]{verbose}[true]{Verbose: #1}
\setkeys{opt}{verbose=true}
\ifPREFIXverbose ON\else OFF\fi
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert "Verbose: true" in out_str
    assert "ON" in out_str


def test_boolkeys_multiple():
    """Test define@boolkeys which creates multiple Boolean keys at once"""
    expander = Expander()

    text = r"""
\makeatletter
\define@boolkeys{opt}[fam@]{key,keytwo,keythree}[true]
\setkeys{opt}{key=true,keytwo=false}
Key: \iffam@key YES\else NO\fi
KeyTwo: \iffam@keytwo YES\else NO\fi
KeyThree: \iffam@keythree YES\else NO\fi
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert "Key: YES" in out_str
    assert "KeyTwo: NO" in out_str
    assert "KeyThree: NO" in out_str  # Not set, defaults to false

    # Test using key name alone (should use default value "true")
    text = r"""
\makeatletter
\define@boolkeys{opt}{verbose,debug,trace}[true]
\setkeys{opt}{verbose,debug=false}
Verbose: \ifKV@opt@verbose ON\else OFF\fi
Debug: \ifKV@opt@debug ON\else OFF\fi
Trace: \ifKV@opt@trace ON\else OFF\fi
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert "Verbose: ON" in out_str  # Used without =, should use default "true"
    assert "Debug: OFF" in out_str
    assert "Trace: OFF" in out_str  # Not set at all
