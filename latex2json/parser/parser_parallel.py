import logging, os
from typing import List, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor
from latex2json.nodes.base_nodes import ASTNode
from latex2json.nodes.bibliography_nodes import BibEntryNode, BibliographyNode
from latex2json.parser.parser import Parser
from latex2json.parser.bib.bib_parser import BibParser
from latex2json.tokens.types import CommandWithArgsToken, Token, TokenType
from latex2json.expander.expander import Expander
from latex2json.tokens.utils import split_tokens_by_predicate


def is_begin_document_token(tok: Token) -> bool:
    return tok.type == TokenType.ENVIRONMENT_START and tok.value == "document"


def is_end_document_token(tok: Token) -> bool:
    return tok.type == TokenType.ENVIRONMENT_END and tok.value == "document"


def is_section_token(tok: Token) -> bool:
    return isinstance(tok, CommandWithArgsToken) and tok.value == "section"


def split_document_tokens(
    tokens: List[Token],
) -> Tuple[List[Token], List[Token], List[Token]]:
    """
    Split tokens into pre-document, document, and post-document sections.

    Args:
        tokens: List of tokens to split

    Returns:
        Tuple of (pre_doc_tokens, doc_tokens, post_doc_tokens)
    """
    pre_doc_tokens = []
    doc_tokens = []
    post_doc_tokens = []

    # first collect pre_doc_tokens
    for i, tok in enumerate(tokens):
        if is_begin_document_token(tok):
            tokens = tokens[i:]
            break
        pre_doc_tokens.append(tok)

    # then parse doc_tokens (check depth)
    depth = 0
    for i, tok in enumerate(tokens):
        if is_begin_document_token(tok):
            depth += 1
        elif is_end_document_token(tok):
            depth -= 1
            if depth == 0:
                doc_tokens = tokens[: i + 1]
                post_doc_tokens = tokens[i + 1 :]
                break
        if depth > 0:
            doc_tokens.append(tok)

    return pre_doc_tokens, doc_tokens, post_doc_tokens


class ParserParallel(Parser):
    """
    Parallel version of LaTeX parser that processes document sections concurrently.

    Extends the base Parser to process document sections in parallel using ProcessPoolExecutor.
    Falls back to sequential processing when only one processor is specified or available.
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        expander: Optional[Expander] = None,
        n_processors: int = 1,
    ):
        super().__init__(logger, expander)
        self.n_processors = n_processors

    # override
    def parse_file(
        self,
        file_path: str,
        postprocess=False,
        resolve_cross_document_references=False,
    ) -> Optional[List[ASTNode]]:
        workers = min(self.n_processors, os.cpu_count())
        if workers <= 1:
            return super().parse_file(
                file_path, postprocess, resolve_cross_document_references
            )

        # set expander cwd
        self.cwd = os.path.abspath(os.path.dirname(file_path))
        tokens = self.expander.expand_file(os.path.basename(file_path))
        if not tokens:
            return None
        self.logger.info(f"Expanded {len(tokens)} tokens from {file_path}, parsing...")

        pre_doc_tokens, doc_tokens, post_doc_tokens = split_document_tokens(tokens)

        self.logger.info(
            "Token counts - Pre doc: %s, Doc: %s, Post doc: %s",
            len(pre_doc_tokens),
            len(doc_tokens),
            len(post_doc_tokens),
        )

        # chunk doc tokens by section split
        doc_tokens = doc_tokens[1:-1]  # strip out begin/end document tokens
        chunks = split_tokens_by_predicate(
            doc_tokens, is_section_token, incl_separator=True, incl_braces=True
        )
        chunks = [pre_doc_tokens] + chunks + [post_doc_tokens]

        # process chunks in parallel
        self.logger.info(
            f"Processing {len(chunks)} sections in parallel with {workers} processors..."
        )
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(ParserParallel._process_standalone, i, tokens, self.cwd)
                for i, tokens in enumerate(chunks)
            ]
            results = []
            for i, future in enumerate(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Chunk {i} processing failed: {e}")
                    results.append([])  # Empty result for failed chunk

        # contain inside regular docnode
        doc_nodes = []
        for nodes in results[1:-1]:
            doc_nodes.extend(nodes)
        doc_node = self.process_text(r"\begin{document}\end{document}")[0]
        doc_node.set_children(doc_nodes)

        out = results[0] + [doc_node] + results[-1]

        if postprocess:
            self.logger.info(f"Postprocessing {len(out)} nodes...")
            out = self.postprocess_nodes(out)

        if resolve_cross_document_references:
            out = self.resolve_crossdoc_node_refs_labels(out)
        return out

    @staticmethod
    def _process_standalone(
        section_idx: int, tokens: List[Token], cwd: str
    ) -> List[ASTNode]:
        print(f"Processing chunk {section_idx} with {len(tokens)} tokens")

        parser = Parser()
        parser.standalone_mode = True
        parser.cwd = cwd
        return parser.process_tokens(tokens)


if __name__ == "__main__":
    from latex2json.nodes.utils import is_whitespace_node, strip_whitespace_nodes

    text = r"""
\begin{document}
\abstract{ABSTRACT}

\section{Section 1}
1111

\section{Section 2}
2222

\end{document}
"""

    parser = ParserParallel(n_processors=2)
    out = parser.parse_file("tests/samples/main.tex", postprocess=True)
    # out = strip_whitespace_nodes(out)
    # out = [node for node in out if not is_whitespace_node(node)]
    # for node in out:
    #     node_meta_str = f"STYLES: {node.styles}"
    #     if node.labels:
    #         node_meta_str += f", LABELS: {node.labels}"
    #     print(node, f"-> {node_meta_str}")
    # out = parser.expander.expand(text)
