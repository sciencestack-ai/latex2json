from latex2json.expander.expander import Expander
from latex2json.tokens.types import EnvironmentStartToken, Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens


def test_at_begin_end_document_handler():
    expander = Expander()
    text = r"""
    \def\aaa{AAA}

    \AtBeginDocument{\def\newaaa{\aaa}} % only expanded at begin document
    \AtEndDocument{END} % executed/returned right before the end document token
    \AtEndDocument{END2} % executed/returned right before the end document token

    \def\aaa{BBB}
    
    \begin{document}
    \newaaa % BBB
    \end{document}
""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out[0] == EnvironmentStartToken("document")
    assert out[-1] == Token(type=TokenType.ENVIRONMENT_END, value="document")

    body_tokens = out[1:-1]
    body_stripped = strip_whitespace_tokens(body_tokens)
    body_str = expander.convert_tokens_to_str(body_stripped)
    assert body_str.startswith("BBB")
