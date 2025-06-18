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
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out == []
