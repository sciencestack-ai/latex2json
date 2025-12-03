import re
from typing import List
import logging

from latex2json.nodes.base_nodes import TextNode
from latex2json.nodes.bibliography_nodes import BibEntryNode, BibType

BEGIN_BIB_PATTERN = re.compile(
    r"\\begin\s*\{(\w*bibliography)\}(.*?)\\end\s*\{\1\}", re.DOTALL
)


class BibItemParser:
    BibItemPattern = re.compile(
        r"\\bibitem\s*(?:\[(.*?)\])?\s*\{(.*?)\}\s*((?:(?!\\bibitem\b)[\s\S])*)",
        re.DOTALL,
    )
    NewblockPattern = re.compile(r"\\newblock\b")

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def can_handle(self, content: str) -> bool:
        # Check for bibliography environment
        if BEGIN_BIB_PATTERN.search(content):
            return True
        # Check for standalone bibitems (existing logic)
        return bool(re.search(r"\\bibitem\b", content))

    def parse(self, content: str) -> List[BibEntryNode]:
        # If content is in bibliography environment, extract the content
        bib_match = BEGIN_BIB_PATTERN.search(content)
        if bib_match:
            content = bib_match.group(2)

        entries = []
        previous_content = None
        bysame_pattern = re.compile(r"\\bysame\b")

        for match in self.BibItemPattern.finditer(content):
            item = match.group(3).strip()
            if item:
                # remove newblock
                item = self.NewblockPattern.sub("", item)

                # Handle \bysame by replacing it with content from previous entry
                if previous_content and bysame_pattern.search(item):
                    # Extract author part from previous entry (up to first comma or --)
                    author_part = re.split(r"[,\-]{1,2}", previous_content)[0]
                    if author_part:
                        # make sure to escape backslashes e.g. \commands, otherwise bad escape \
                        item = bysame_pattern.sub(
                            author_part.replace("\\", "\\\\"), item
                        )

                entry = BibEntryNode(
                    citation_key=match.group(2).strip(),
                    content=[TextNode(item)],
                    label=match.group(1).strip() if match.group(1) else None,
                    format=BibType.BIBITEM,
                    fields={},
                )
                entries.append(entry)
                previous_content = item
        return entries
