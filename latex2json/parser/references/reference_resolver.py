from dataclasses import dataclass
from typing import Dict, List
from latex2json.nodes import ASTNode, RefNode
from latex2json.parser.parser_core import ParserCore
from latex2json.utils.tex_utils import strip_tex_extension


@dataclass
class ReferenceRegistry:
    filename: str
    # all registered labels for this document/filename
    labels: List[str]
    # prefix mappings for external documents via \externaldocument[prefix]{filename}
    external_documents_prefixes: Dict[str, str]
    # new prefix to be assigned to refs/labels of this document/filename
    new_prefix: str = ""

    def is_label_in_registry(self, label: str) -> bool:
        return label in self.labels

    def assign_new_prefix(self, label: str) -> str:
        if label.startswith(self.new_prefix):
            return label
        return self.new_prefix + label


def resolve_node_references_and_labels(
    nodes: List[ASTNode],
    reference_registries: Dict[str, ReferenceRegistry],
    recurse=True,
):
    """
    - Iterate over RefNodes and check its .source_file to match with external_documents_prefixes
    - Iterate over labels and assign new prefix if needed
    Goal: To keep labels and references 1-1 for cross document nodes
    """

    if not reference_registries:
        return

    for node in nodes:
        # get source file str to know what it came from, and match with external_documents_prefixes
        source_file = node.get_source_file()

        if source_file:
            filename = strip_tex_extension(source_file)
            registry = reference_registries.get(filename)
            if registry:
                if isinstance(node, RefNode):
                    references = node.references
                    prefixes = registry.external_documents_prefixes

                    for i, ref in enumerate(references):
                        if registry.is_label_in_registry(ref):
                            # local reference. Assign local new prefix
                            references[i] = registry.assign_new_prefix(ref)
                        else:
                            # external reference. Check if it has a prefix
                            for external_filename, prefix in prefixes.items():
                                if ref.startswith(prefix):
                                    xref = ref.replace(prefix, "", 1)
                                    # check if ref_stripped is in external registry
                                    external_registry = reference_registries.get(
                                        external_filename
                                    )
                                    if not external_registry:
                                        # find across all other registries
                                        for k, reg in reference_registries.items():
                                            if reg != registry:
                                                if reg.is_label_in_registry(xref):
                                                    external_registry = reg
                                                    break

                                    if external_registry:
                                        references[i] = (
                                            external_registry.assign_new_prefix(xref)
                                        )

                                    break

            if node.labels:
                if registry:
                    # assign new prefix to labels
                    node.labels = [
                        registry.assign_new_prefix(label) for label in node.labels
                    ]
                else:
                    # find across all other registries
                    for i, label in enumerate(node.labels):
                        for k, reg in reference_registries.items():
                            if reg.is_label_in_registry(label):
                                node.labels[i] = [
                                    reg.assign_new_prefix(label)
                                    for label in node.labels
                                ]
                                break

        if recurse:
            if node.children:
                resolve_node_references_and_labels(
                    node.children, reference_registries, recurse
                )


def generate_reference_registries(parser: ParserCore) -> Dict[str, ReferenceRegistry]:
    """
    label_registry = {'manuscript': ['sec:main'],
    'intro': ['sec:intro', 'M-M-sec:fake'],
    'appendix': ['sec:appendix']}

    external_documents_prefixes = {'intro': {'manuscript': 'M-'}, 'appendix': {'intro': 'I-'}}
    """
    label_registry = {
        strip_tex_extension(k): v for k, v in parser.label_registry.items()
    }
    external_documents_prefixes = {
        strip_tex_extension(k): v for k, v in parser.external_documents_prefixes.items()
    }

    reference_registries: Dict[str, ReferenceRegistry] = {}
    for filename, labels in label_registry.items():
        new_prefix = filename + ":"
        reference_registries[filename] = ReferenceRegistry(
            filename,
            labels,
            external_documents_prefixes.get(filename, {}),
            new_prefix=new_prefix,
        )

    return reference_registries
