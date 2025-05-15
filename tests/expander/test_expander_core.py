import pytest

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.expander.state import ExpanderState, StateLayer, ProcessingMode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.tokenizer import Tokenizer


def test_expander_core():
    expander = ExpanderCore()
