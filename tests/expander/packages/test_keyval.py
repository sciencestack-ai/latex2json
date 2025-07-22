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
