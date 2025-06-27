from typing import Dict, List, Optional
from latex2json.nodes.base_nodes import ASTNode, TextNode


def convert_fields_to_bibtex_str(
    entry_type: str, citation_key: str, fields: Dict[str, str]
) -> str:
    """Convert fields to BibTeX string"""
    content = ",\n\t".join(f"{k}={{{v}}}" for k, v in fields.items())
    return f"@{entry_type}{{{citation_key},\n\t{content}\n}}"


class BibEntryNode(ASTNode):
    def __init__(
        self,
        citation_key: str,
        content: List[ASTNode] = [],
        format: str = "bibtex",
        label: Optional[str] = None,  # for bibitem e.g. \bibitem[...label...]{}
        # bibtex related below
        entry_type: Optional[str] = None,  # e.g. article/proceedings/etc.
        fields: Dict[str, str] = {},  # for bibtex e.g. author, title, etc.
    ):
        super().__init__()
        self.citation_key = citation_key
        self.label = label
        self.format = format
        self.set_body(content)

        # BibTeX related below
        self.entry_type = entry_type
        self.fields = fields

    @property
    def body(self) -> List[ASTNode]:
        return self.children

    def set_body(self, body: List[ASTNode]):
        self.set_children(body)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, BibEntryNode):
            return False
        if self.citation_key != other.citation_key:
            return False
        if self.label != other.label:
            return False
        if self.format != other.format:
            return False
        if self.entry_type != other.entry_type:
            return False
        if self.fields != other.fields:
            return False
        return all(a == b for a, b in zip(self.children, other.children))

    def detokenize(self) -> str:
        out_str = ""
        if self.format == "bibitem":
            out_str = f"\\bibitem"
            if self.label:
                out_str += f"[{self.label}]"
            out_str += "{" + self.citation_key + "}"
            out_str += "\n"
        content = "".join(child.detokenize() for child in self.children)
        out_str += content + "\n"
        return out_str

    def __str__(self):
        return self.detokenize()

    def get_author_str(self):
        if self.format == "bibitem":
            content = "".join(child.detokenize() for child in self.children).strip()
            if "," in content:
                return content.split(",")[0]

        author_field = self.fields.get("author") or self.fields.get("authors")
        if not author_field:
            return None
        return author_field

    @classmethod
    def from_bibtex(
        cls, entry_type: str, citation_key: str, fields: Dict[str, str]
    ) -> "BibEntryNode":
        """Convert BibTeX entry to bibliography entry"""
        # Format content as string representation of fields
        content = convert_fields_to_bibtex_str(entry_type, citation_key, fields)

        return cls(
            entry_type=entry_type,
            citation_key=citation_key,
            content=[TextNode(content)],
            fields=fields,
        )

    def to_json(self):
        result = super().to_json()
        result["type"] = "bibitem"
        result["key"] = self.citation_key
        result["format"] = self.format
        result["content"] = [child.to_json() for child in self.children]
        if self.label:
            result["label"] = self.label
        if self.fields:
            result["fields"] = self.fields
        return result


class BibliographyNode(ASTNode):
    def __init__(
        self,
        bib_items: List[BibEntryNode] = [],
    ):
        super().__init__()
        self.bib_items = bib_items
        self.set_children(bib_items)

    def add_item(self, item: BibEntryNode):
        self.bib_items.append(item)
        self.set_children(self.bib_items)

    def is_empty(self) -> bool:
        """Check if this is an empty list."""
        return len(self.bib_items) == 0

    def __eq__(self, other: ASTNode):
        if not isinstance(other, BibliographyNode):
            return False
        return all(a == b for a, b in zip(self.bib_items, other.bib_items))

    def detokenize(self) -> str:
        """Convert the list node back to LaTeX source code."""
        if not self.bib_items:
            return f"\\begin{{thebibliography}}\\end{{thebibliography}}"

        out = f"\\begin{{thebibliography}}\n"

        for item in self.bib_items:
            out += item.detokenize() + "\n"

        out += f"\\end{{thebibliography}}"
        return out

    def __str__(self):
        return self.detokenize()

    def to_json(self):
        result = super().to_json()
        result["type"] = "bibliography"
        result["content"] = [item.to_json() for item in self.bib_items]
        return result
