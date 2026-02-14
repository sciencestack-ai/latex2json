from typing import Dict, List, Optional
from latex2json.nodes.base_nodes import ASTNode, TextNode
from latex2json.nodes.node_types import BibType, NodeTypes


def convert_fields_to_bibtex_str(
    entry_type: str, citation_key: str, fields: Dict[str, str]
) -> str:
    """Convert fields to BibTeX string"""
    content = ",\n\t".join(f"{k}={{{v}}}" for k, v in fields.items())
    return f"@{entry_type}{{{citation_key},\n\t{content}\n}}"


class BibEntryNode(ASTNode):
    __slots__ = ('citation_key', 'label', 'format', 'entry_type', 'fields')

    def __init__(
        self,
        citation_key: str,
        content: Optional[List[ASTNode]] = None,
        format: str = BibType.BIBTEX,
        label: Optional[str] = None,  # for bibitem e.g. \bibitem[...label...]{}
        # bibtex related below
        entry_type: Optional[str] = None,  # e.g. article/proceedings/etc.
        fields: Optional[Dict[str, str]] = None,  # for bibtex e.g. author, title, etc.
    ):
        super().__init__()
        self.citation_key = citation_key
        if format == BibType.BIBITEM:
            # in latex, internally anchor 'cite.{citation_key}' is created per bibitem
            item_label = f"cite.{citation_key}"
            # Use _labels directly to avoid property overhead
            if self._labels is None:
                self._labels = [item_label]
            else:
                self._labels.append(item_label)
        self.label = label
        self.format = format
        self.set_body(content if content is not None else [])

        # BibTeX related below
        self.entry_type = entry_type
        self.fields = fields if fields is not None else {}

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
        if self.format == BibType.BIBITEM:
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
        if self.format == BibType.BIBITEM:
            content = "".join(child.detokenize() for child in self.children).strip()
            comma_idx = content.find(",")
            dash_idx = content.find("--")

            if comma_idx >= 0 and (dash_idx < 0 or comma_idx < dash_idx):
                return content[:comma_idx].strip()
            elif dash_idx >= 0:
                return content[:dash_idx].strip()

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
        result["type"] = NodeTypes.BIBITEM
        result["key"] = self.citation_key
        if self.entry_type:
            result["entry_type"] = self.entry_type
        result["format"] = self.format
        result["content"] = [child.to_json() for child in self.children]
        if self.label:
            result["label"] = self.label
        if self.fields:
            result["fields"] = self.fields
        return result

    def copy(self):
        return BibEntryNode(
            citation_key=self.citation_key,
            content=self.copy_nodes(self.children),
            format=self.format,
            label=self.label,
            entry_type=self.entry_type,
            fields=self.fields,
        )


class BibliographyNode(ASTNode):
    __slots__ = ('bib_items',)

    def __init__(
        self,
        bib_items: Optional[List[BibEntryNode]] = None,
    ):
        super().__init__()
        self.bib_items = bib_items if bib_items is not None else []
        self.set_children(self.bib_items)

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
        result["type"] = NodeTypes.BIBLIOGRAPHY
        result["content"] = [item.to_json() for item in self.bib_items]
        return result

    def copy(self):
        return BibliographyNode(self.copy_nodes(self.bib_items))
