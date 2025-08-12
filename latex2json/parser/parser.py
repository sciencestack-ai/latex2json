import logging, os
from typing import List, Optional
from latex2json.nodes.base_nodes import ASTNode
from latex2json.nodes.bibliography_nodes import BibEntryNode, BibliographyNode
from latex2json.parser.parser_core import ParserCore
from latex2json.parser.bib.bib_parser import BibParser
from latex2json.tokens.types import Token
from latex2json.expander.expander import Expander


class Parser(ParserCore):
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        expander: Optional[Expander] = None,
    ):
        super().__init__(logger, expander)

        self.bib_parser = BibParser(logger=self.logger)

        self._register_handlers()

    def _register_handlers(self):
        from latex2json.parser.handlers import register_handlers

        register_handlers(self)

        self._register_bib_handlers()

    def _register_bib_handlers(self):
        def bib_file_handler(parser: Parser, token: Token) -> List[BibliographyNode]:
            parser.skip_whitespace()
            bib_path_str = parser.parse_brace_name()
            if not bib_path_str:
                parser.logger.warning(f"No bib path found")
                return []
            bib_items = parser.parse_bib_file(bib_path_str)

            return [BibliographyNode(bib_items=bib_items)]

        for cmd in ["bibliography", "addbibresource"]:
            self.register_handler(cmd, bib_file_handler)

    def parse_file(self, file_path: str, postprocess=False) -> Optional[List[ASTNode]]:
        # set expander cwd
        self.cwd = os.path.abspath(os.path.dirname(file_path))
        tokens = self.expander.expand_file(os.path.basename(file_path))
        if not tokens:
            return None
        self.logger.info(f"Expanded {len(tokens)} tokens from {file_path}, parsing...")
        out = self.process_tokens_standalone(tokens)
        if postprocess:
            self.logger.info(f"Postprocessing {len(out)} nodes...")
            out = self.postprocess_nodes(out)
        return out

    def parse_bib_file(self, file_path: str) -> List[BibEntryNode]:
        all_entries: List[BibEntryNode] = []

        # Handle comma-separated list of files or single file
        file_paths = [p.strip() for p in file_path.split(",") if p.strip()]

        for path in file_paths:
            # Apply current_file_dir to each path
            full_path = path
            if not os.path.isabs(full_path):
                full_path = os.path.join(self.cwd, full_path)

            try:
                entries = self.bib_parser.parse_file(full_path)
                all_entries.extend(entries)
            except Exception as e:
                self.logger.warning(
                    f"Failed to parse bibliography file: {full_path}, error: {str(e)}"
                )

        # check and remove duplicate cite_keys
        cite_keys = set()
        non_duplicate_entries: List[BibEntryNode] = []
        for entry in all_entries:
            if entry.citation_key in cite_keys:
                continue
            cite_keys.add(entry.citation_key)
            non_duplicate_entries.append(entry)

        # process each bibitem with parser to ensure all latex commands are expanded
        bib_items = []
        for i, item in enumerate(non_duplicate_entries):
            if item.format == "bibitem":
                content_str = self.convert_nodes_to_str(item.body)
                # process the content_str
                formatted_nodes = self.process_text(content_str)
                item.set_body(formatted_nodes)
                bib_items.append(item)
            else:
                fields = item.fields
                for k, v in fields.items():
                    formatted_nodes = self.process_text(v)
                    fields[k] = self.convert_nodes_to_str(formatted_nodes)
                entry = BibEntryNode.from_bibtex(
                    entry_type=item.entry_type,
                    citation_key=item.citation_key,
                    fields=fields,
                )
                bib_items.append(entry)
        return bib_items


if __name__ == "__main__":
    from latex2json.nodes.utils import is_whitespace_node, strip_whitespace_nodes

    samples_dir = os.path.dirname(os.path.abspath(__file__)) + "/../../tests/samples"
    #     text = r"""
    #     PRE BIBLIOGRAPHY

    #     \bibliography{%s/bibtex, %s/bib.bbl}

    #     POST BIBLIOGRAPHY
    # """ % (
    #         samples_dir,
    #         samples_dir,
    #     )

    text = r"""
\renewenvironment{abstract}%
{%
  \begin{quote}%
}
{
  \end{quote}%
}

\begin{abstract}
ABSTRACT
\end{abstract}
"""

    parser = Parser(prevent_whitelisted_redefinitions=False)
    out = parser.parse(text, postprocess=True)
    # out = strip_whitespace_nodes(out)
    # out = [node for node in out if not is_whitespace_node(node)]
    # for node in out:
    #     node_meta_str = f"STYLES: {node.styles}"
    #     if node.labels:
    #         node_meta_str += f", LABELS: {node.labels}"
    #     print(node, f"-> {node_meta_str}")
    # out = parser.expander.expand(text)
