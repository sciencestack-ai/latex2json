from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token


def test_xpatch_cmds():
    # same as etoolbox_patchcmds, but using xpatch commands

    expander = Expander()

    text = r"""
    \makeatletter

    \def\foo{foo}
    \xpatchcmd{\foo}{o}{ MIDDLE O }{success}{failure}

    \foo % foo -> f MIDDLE O o

    \xpretocmd{\foo}{prepend }{success}{failure}
    \foo % f MIDDLE O o -> prepend f MIDDLE O o

    \xapptocmd{\foo}{ append}{success}{failure}
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
