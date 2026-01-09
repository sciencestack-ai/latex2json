"""
AMSTeX to LaTeX token-based preprocessor.

Transforms AMSTeX-specific constructs into standard LaTeX tokens
before passing to the main expander.
"""

from logging import Logger
from typing import List, Optional

from latex2json.tokens import Catcode, Token, TokenType, Tokenizer
from latex2json.expander.token_processor import TokenProcessor
from latex2json.tokens.utils import wrap_tokens_in_braces


class AMSTeXExpander(TokenProcessor):
    """
    Token-based preprocessor for AMSTeX documents.

    Transforms AMSTeX commands into their LaTeX equivalents:
    - \\document -> \\begin{document}
    - \\enddocument -> \\end{document}
    - \\proclaim{...} -> \\begin{proclaim}{...}
    - \\endproclaim -> \\end{proclaim}
    - etc.
    """

    # AMSTeX environment pairs: maps (cmd_name, end_cmd_name) -> env_name
    # \cmd -> \begin{env}, \end_cmd -> \end{env}
    ENVIRONMENT_PAIRS = {
        # Core
        ("document", "enddocument"): "document",
        ("topmatter", "endtopmatter"): "topmatter",
        ("roster", "endroster"): "itemize",
        ("Refs", "endRefs"): "thebibliography",
        # Theorem-like
        ("definition", "enddefinition"): "definition",
        ("lemma", "endlemma"): "lemma",
        ("corollary", "endcorollary"): "corollary",
        ("proposition", "endproposition"): "proposition",
        ("remark", "endremark"): "remark",
        ("example", "endexample"): "example",
        # Proof
        ("demo", "enddemo"): "proof",
    }

    # Commands that should be removed (no-ops)
    REMOVE_COMMANDS = {
        "nologo",
        "NoBlackBoxes",
        "BlackBoxes",
        "TagsOnRight",
        "TagsOnLeft",
        "TagsAsMath",
        "endref",
    }

    # Simple command replacements (amstex -> latex)
    SIMPLE_REPLACEMENTS = {
        # sections
        "heading": "section",
        "subheading": "subsection",
        # bib
        "ref": "bibitem",
        #
        "define": "def",
        "redefine": "def",
        # styles
        "bold": "mathbf",
        "Bold": "mathbf",
        "Cal": "mathcal",
        "Bbb": "mathbb",
        "frak": "mathfrak",
        "goth": "mathfrak",
        "ssf": "mathsf",
        "smc": "textsc",
        "rom": "textrm",
        "dsize": "displaystyle",
    }

    def __init__(
        self,
        tokenizer: Optional[Tokenizer] = None,
        logger: Optional[Logger] = None,
    ):
        super().__init__(tokenizer=tokenizer, logger=logger)
        self._register_handlers()

    def _register_handlers(self):
        """Register handlers for all AMSTeX commands."""
        # Register environment pairs (both begin and end)
        for (begin_cmd, end_cmd), env_name in self.ENVIRONMENT_PAIRS.items():
            self._register_environment_pair(begin_cmd, end_cmd, env_name)

        # Register removal commands
        for cmd_name in self.REMOVE_COMMANDS:
            self.register_handler(f"\\{cmd_name}", self._make_remove_handler())

        # Register simple replacements
        for amstex_cmd, latex_cmd in self.SIMPLE_REPLACEMENTS.items():
            self._register_replacement_handler(amstex_cmd, latex_cmd)

        # # custom logic for \proclaim
        # def proclaim_handler(processor: "AMSTeXExpander", token: Token) -> List[Token]:
        #     return [token]

        # self.register_handler("\\proclaim", proclaim_handler)
        # self.register_handler("\\endproclaim", proclaim_handler)

        # custom logic for \key
        def key_handler(processor: "AMSTeXExpander", token: Token) -> List[Token]:
            # convert to simply {...}
            processor.skip_whitespace()
            citekey = processor.parse_tokens_until(
                predicate=lambda t: t.catcode != Catcode.LETTER
            )
            return wrap_tokens_in_braces(citekey)

        self.register_handler("\\key", key_handler)

    def _register_environment_pair(self, begin_cmd: str, end_cmd: str, env_name: str):
        """Register handlers for both \\cmd -> \\begin{env} and \\endcmd -> \\end{env}."""

        def begin_handler(processor: "AMSTeXExpander", token: Token) -> List[Token]:
            return processor._make_begin_tokens(env_name)

        def end_handler(processor: "AMSTeXExpander", token: Token) -> List[Token]:
            return processor._make_end_tokens(env_name)

        self.register_handler(f"\\{begin_cmd}", begin_handler)
        self.register_handler(f"\\{end_cmd}", end_handler)

    def _register_replacement_handler(self, amstex_cmd: str, latex_cmd: str):
        """Register a handler that transforms \\amstex -> \\latex."""

        def handler(processor: "AMSTeXExpander", token: Token) -> List[Token]:
            return [Token(TokenType.CONTROL_SEQUENCE, latex_cmd)]

        self.register_handler(f"\\{amstex_cmd}", handler)

    def _make_remove_handler(self):
        """Create a handler that removes the command (returns empty list)."""

        def handler(processor: "AMSTeXExpander", token: Token) -> List[Token]:
            return []

        return handler

    def _make_begin_tokens(self, env_name: str) -> List[Token]:
        """Create tokens for \\begin{env_name}."""
        env_tokens = [
            Token(TokenType.CHARACTER, char, catcode=Catcode.LETTER)
            for char in env_name
        ]
        return [Token(TokenType.CONTROL_SEQUENCE, "begin")] + wrap_tokens_in_braces(
            env_tokens
        )

    def _make_end_tokens(self, env_name: str) -> List[Token]:
        """Create tokens for \\end{env_name}."""
        env_tokens = [
            Token(TokenType.CHARACTER, char, catcode=Catcode.LETTER)
            for char in env_name
        ]
        return [Token(TokenType.CONTROL_SEQUENCE, "end")] + wrap_tokens_in_braces(
            env_tokens
        )


if __name__ == "__main__":
    expander = AMSTeXExpander()
    text = r"""

\input amstex

\document
\nologo
\NoBlackBoxes
\TagsOnRight
\define\h{\text{H}}
\define\Q{\bold Q}
\define\C{\bold C}
\define\Z{\bold Z}

\subheading{ Comparision of symplectic and complex geometry}


\Refs

\ref \key AM\by P. S. Aspinwall, D. R. Morrison \paper
 Topological field theory and rational curves \jour Commun. Math. Phys. \pages
245--262\yr 1993 \vol 151\endref

\endRefs


\enddocument
"""
    tokens = expander.process_text(text)
    out_str = expander.convert_tokens_to_str(tokens).strip()
    print(out_str)
