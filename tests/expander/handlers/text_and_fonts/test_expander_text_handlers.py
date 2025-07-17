import pytest
from latex2json.expander.expander import Expander
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType


def test_textcommands_braces():
    expander = Expander()
    text = r"\textbf abcd"
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out)
    assert out_str == r"\textbf{a}bcd"


def test_textcommands_in_mathmode():
    expander = Expander()
    text = r"$_\textbf{_$1+1$}_$"
    out = expander.expand(text)
    # evaluates to same string
    out_str = expander.convert_tokens_to_str(out)
    assert out_str == text

    textmode_subscript_catcode = Catcode.SUBSCRIPT
    mathmode_subscript_catcode = Catcode.ACTIVE

    # but check the tokens are different due to math/text mode, esp the '_'
    assert out[0].to_str() == "$" and out[-1].to_str() == "$"
    # $_... -> _ is mathmode
    assert out[1] == Token(
        type=TokenType.CHARACTER, value="_", catcode=mathmode_subscript_catcode
    )
    # ... _$ -> _ is also mathmode since it is outside \textbf{}
    assert out[-2] == Token(
        type=TokenType.CHARACTER, value="_", catcode=mathmode_subscript_catcode
    )

    assert out[2] == Token(type=TokenType.CONTROL_SEQUENCE, value="textbf")
    assert out[3] == Token(
        type=TokenType.CHARACTER, value="{", catcode=Catcode.BEGIN_GROUP
    )
    # # check the subscript right after \textbf is SUBSCRIPT i.e. textmode catcode
    assert out[4] == Token(
        type=TokenType.CHARACTER, value="_", catcode=textmode_subscript_catcode
    )
