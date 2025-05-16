import pytest

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.expander.state import ExpanderState, StateLayer, ProcessingMode
from latex2json.nodes.syntactic_nodes import TextNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.tokenizer import Tokenizer
from tests.parser.test_parser_core import assert_ast_sequence


def test_expander_core():
    expander = ExpanderCore()

    expander.set_text("{abcd}")
    ast = expander.process()
    assert_ast_sequence(ast, [TextNode("abcd")])
