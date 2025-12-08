from dataclasses import dataclass
from enum import Enum
from logging import Logger
import logging
import re
from typing import Dict, List, Optional
from latex2json.nodes.bibliography_nodes import BibEntryNode
from latex2json.parser.bib.compiled_bibtex import (
    is_compiled_bibtex,
    process_compiled_bibtex_to_bibtex,
)
from latex2json.utils.tex_utils import extract_braced_content_fast


BibTexPattern = re.compile(r"@(\w+)\s*\{")
BibTexFieldPattern = re.compile(r"(\w+)\s*=\s*")


class BibTexParser:
    def __init__(self, logger: Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    @staticmethod
    def can_handle(content: str) -> bool:
        """Check if this parser can handle the given content.

        Args:
            content: The content to check

        Returns:
            bool: True if content can be handled by this parser
        """
        return BibTexParser.is_bibtex(content) or is_compiled_bibtex(content)

    @staticmethod
    def is_bibtex(content: str) -> bool:
        """Check if the content is in standard BibTeX format.

        Args:
            content: The content to check

        Returns:
            bool: True if content is in BibTeX format, False otherwise
        """
        return bool(BibTexPattern.search(content))

    @staticmethod
    def convert_fields_to_bibtex_str(
        entry_type: str, citation_key: str, fields: Dict[str, str]
    ) -> str:
        """Convert fields to BibTeX string"""
        content = ",\n\t".join(f"{k}={{{v}}}" for k, v in fields.items())
        return f"@{entry_type}{{{citation_key},\n\t{content}\n}}"

    def parse(self, content: str) -> List[BibEntryNode]:
        """Parse BibTeX content and return list of BibEntry objects"""
        self.logger.debug("Starting BibTeX parsing")

        # Check if this is compiled BibTeX and convert if needed
        if is_compiled_bibtex(content):
            self.logger.info(
                "Detected compiled BibTeX format, converting to standard BibTeX"
            )
            bibtex_entries = process_compiled_bibtex_to_bibtex(content)
            content = "\n".join(bibtex_entries)

        entries = []

        # Optimization: Find all entry positions in one pass
        entry_matches = list(re.finditer(BibTexPattern, content))
        total_entries = len(entry_matches)

        if total_entries > 1000:
            self.logger.info(f"Parsing {total_entries} BibTeX entries (this may take a moment)...")

        # Process each entry
        for idx, match in enumerate(entry_matches):
            # Log progress for large files
            if total_entries > 1000 and idx > 0 and idx % 10000 == 0:
                self.logger.info(f"Progress: {idx}/{total_entries} entries parsed ({idx*100//total_entries}%)")

            entry_type = match.group(1).lower()
            entry_start = match.end() - 1  # Position of the opening brace

            # Fast extraction without escape checking (BibTeX rarely has escaped braces)
            entry_content, _ = extract_braced_content_fast(content, entry_start)
            if entry_content is None:
                continue

            # Split into citation key and fields
            key_end = entry_content.find(",")
            if key_end == -1:
                continue

            citation_key = entry_content[:key_end].strip()
            fields_text = entry_content[key_end + 1 :].strip()

            # Parse fields - optimized to avoid repeated substring operations
            fields = self._parse_fields_optimized(fields_text)

            entry = BibEntryNode.from_bibtex(
                entry_type=entry_type, citation_key=citation_key, fields=fields
            )
            entries.append(entry)

        return entries

    def _parse_fields_optimized(self, fields_text: str) -> Dict[str, str]:
        """Optimized field parsing that minimizes substring operations"""
        fields = {}
        pos = 0
        text_len = len(fields_text)

        while pos < text_len:
            # Find next field pattern from current position
            field_match = BibTexFieldPattern.search(fields_text, pos)
            if not field_match:
                break

            field_name = field_match.group(1).lower()
            field_start = field_match.end()

            # Skip whitespace
            while field_start < text_len and fields_text[field_start].isspace():
                field_start += 1

            if field_start >= text_len:
                break

            # Get value - either in braces or quotes
            if fields_text[field_start] == "{":
                # Use fast brace extraction
                value, value_end = extract_braced_content_fast(fields_text, field_start)
                if value is not None:
                    fields[field_name] = value.strip()
                    pos = value_end
                else:
                    break
            elif fields_text[field_start] == '"':
                # Find closing quote
                end_quote = field_start + 1
                while end_quote < text_len and fields_text[end_quote] != '"':
                    end_quote += 1
                if end_quote < text_len:
                    fields[field_name] = fields_text[field_start + 1:end_quote]
                    pos = end_quote + 1
                else:
                    break
            else:
                # Skip this field if malformed
                pos = field_start + 1
                continue

            # Skip trailing comma and whitespace
            while pos < text_len and (fields_text[pos].isspace() or fields_text[pos] == ","):
                pos += 1

        return fields


if __name__ == "__main__":
    parser = BibTexParser()
    # For BibTeX content
    bibtex_content = """
    @article{key1,
    title={Some Title},
    author={Author Name},
    year={2023}
    }
    """
    entries = parser.parse(bibtex_content)
    print(entries)
