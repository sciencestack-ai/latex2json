"""
AMSTeX to LaTeX token-based preprocessor.

Transforms AMSTeX-specific constructs into standard LaTeX tokens
before passing to the main expander.
"""

from logging import Logger
from typing import List, Optional

from latex2json.tokens import Catcode, Token, TokenType, Tokenizer
from latex2json.expander.token_processor import TokenProcessor


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
        ("proclaim", "endproclaim"): "proclaim",
        ("definition", "enddefinition"): "definition",
        ("lemma", "endlemma"): "lemma",
        ("corollary", "endcorollary"): "corollary",
        ("proposition", "endproposition"): "proposition",
        ("remark", "endremark"): "remark",
        ("example", "endexample"): "example",
        # Proof
        ("demo", "enddemo"): "proof",
        # Sectioning (these take an argument)
        ("heading", "endheading"): "heading",
        ("subheading", "endsubheading"): "subheading",
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
        "define": "def",
        "redefine": "def",
        "bold": "mathbf",
        "Bold": "mathbf",
        "Cal": "mathcal",
        "Bbb": "mathbb",
        "frak": "mathfrak",
        "goth": "mathfrak",
        "ssf": "mathsf",
        "smc": "textsc",
        "rom": "textrm",
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
        tokens = [
            Token(TokenType.CONTROL_SEQUENCE, "begin"),
            Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
        ]
        for char in env_name:
            tokens.append(Token(TokenType.CHARACTER, char, catcode=Catcode.LETTER))
        tokens.append(Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP))
        return tokens

    def _make_end_tokens(self, env_name: str) -> List[Token]:
        """Create tokens for \\end{env_name}."""
        tokens = [
            Token(TokenType.CONTROL_SEQUENCE, "end"),
            Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP),
        ]
        for char in env_name:
            tokens.append(Token(TokenType.CHARACTER, char, catcode=Catcode.LETTER))
        tokens.append(Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP))
        return tokens
