import logging, os
from typing import List, Optional
from latex2json.nodes.bibliography_nodes import BibEntryNode, BibliographyNode
from latex2json.parser.parser_core import ParserCore
from latex2json.parser.bib.bib_parser import BibParser
from latex2json.tokens.types import Token


class Parser(ParserCore):
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__(logger)

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

    def parse_bib_file(self, file_path: str) -> List[BibEntryNode]:
        bib_items = self.bib_parser.parse_file(file_path)

        # process each bibitem with parser to ensure all latex commands are expanded
        for i, item in enumerate(bib_items):
            if item.format == "bibitem":
                content_str = parser.convert_nodes_to_str(item.body)
                # process the content_str
                formatted_nodes = parser.process_text(content_str)
                item.set_body(formatted_nodes)
            else:
                fields = item.fields
                for k, v in fields.items():
                    formatted_nodes = parser.process_text(v)
                    fields[k] = parser.convert_nodes_to_str(formatted_nodes)
                bib_items[i] = BibEntryNode.from_bibtex(
                    entry_type=item.entry_type,
                    citation_key=item.citation_key,
                    fields=fields,
                )
        return bib_items


if __name__ == "__main__":
    from latex2json.nodes.utils import is_whitespace_node, strip_whitespace_nodes

    text = r"""
    PRE BIBLIOGRAPHY

    \bibliography{%s/bibtex}

    POST BIBLIOGRAPHY
""" % (
        os.path.dirname(os.path.abspath(__file__)) + "/../../tests/samples"
    )

    parser = Parser()
    out = parser.parse(text, postprocess=True)
    # out = strip_whitespace_nodes(out)
    # out = [node for node in out if not is_whitespace_node(node)]
    # for node in out:
    #     node_meta_str = f"STYLES: {node.styles}"
    #     if node.labels:
    #         node_meta_str += f", LABELS: {node.labels}"
    #     print(node, f"-> {node_meta_str}")
    # out = parser.expander.expand(text)
