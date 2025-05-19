import pytest

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.expander.state import ExpanderState, StateLayer, ProcessingMode
from latex2json.nodes.syntactic_nodes import BraceNode, TextNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.tokenizer import Tokenizer
from tests.test_utils import assert_ast_sequence


# def test_expander_core():
#     expander = ExpanderCore()

#     expander.set_text("{{abcd}}")
#     ast = expander.process()
#     assert_ast_sequence(ast, [TextNode("abcd")])


# def test_parse_brace_group():
#     text = r"""{OUTER{INNER}POST}"""

#     expander = ExpanderCore()
#     expander.set_text(text)
#     expander.parser.parse_element()  # parse beginning brace...
#     brace_group = expander.parse_brace_group()
#     assert brace_group == BraceNode(
#         [
#             TextNode("OUTER"),
#             BraceNode(
#                 [
#                     TextNode("INNER"),
#                 ]
#             ),
#             TextNode("POST"),
#         ]
#     )
