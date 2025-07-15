import pytest

from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens
from tests.test_utils import assert_token_sequence


def test_for_do_handler():
    expander = Expander()

    # first use \makeatletter for @
    expander.expand(r"\makeatletter")

    def test_without_braces():
        # test base case without {}
        text = r"""
        \@for\@tempa:=-1,0,1,2,3,4,5\do{ 
        \@tempa
        }
        """
        out = expander.expand(text)
        strip_whitespace_tokens(out)

        out_str = expander.convert_tokens_to_str(out).strip()
        out_str = out_str.replace("\n", "").replace(" ", "")
        assert out_str == "-1012345"

    def test_with_braces():
        text = r"""
        \def\xxx#1{*#1*} % this is done to check that the \item macro is expanded correctly
        \@for\item:={apple,banana,cherry}\do{%
            \xxx\item % \item is a macro, so this will be expanded to \xxx\item -> *\item* -> *apple*, and NOT \xxxapple -> *a*pple
        }"""
        out = expander.expand(text)

        out_str = expander.convert_tokens_to_str(out).strip()
        out_str = out_str.replace("\n", "").replace(" ", "")
        assert out_str == "*apple**banana**cherry*"

    def test_variable_macro_scoping():
        # let's define \def\item{ITEM} first in the same scope and see that it is deleted after the loop using \item var name
        expander.expand(r"\def\myvar{VAR}")

        assert expander.get_macro("myvar")

        text = r"""
        \@for\myvar:={apple,banana,cherry}\do{%
            \xxx\myvar 
        }"""
        out = expander.expand(text)

        # ensure the \item macro is deleted after the loop since it shares the same scope
        assert not expander.get_macro("myvar")

        # HOWEVER, ensure it is not deleted if global or a higher scope
        text = r"""
        \def\myvar{VAR}
        {
            % new scope
            \@for\myvar:={apple,banana,cherry}\do{%
                \xxx\myvar 
            }
        }
        """
        out = expander.expand(text)
        assert expander.get_macro("myvar")
        assert expander.expand(r"\myvar") == expander.convert_str_to_tokens("VAR")

    test_without_braces()
    test_with_braces()
    test_variable_macro_scoping()
