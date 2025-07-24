from contextvars import Token
from typing import List
from latex2json.nodes import (
    ASTNode,
    CommandNode,
    AuthorNode,
    AuthorsNode,
    MetadataNode,
    NodeTypes,
)
from latex2json.nodes.utils import split_nodes_by_predicate, strip_whitespace_nodes
from latex2json.parser.parser_core import ParserCore


def and_command_predicate(cmd: ASTNode):
    return isinstance(cmd, CommandNode) and cmd.name.lower() == "and"


def author_handler(parser: ParserCore, token: Token):
    parser.skip_whitespace()
    short = parser.parse_bracket_as_nodes()
    parser.skip_whitespace()
    long = parser.parse_brace_as_nodes()

    if not long:
        return []

    authors = split_nodes_by_predicate(long, and_command_predicate)
    author_nodes: List[AuthorNode] = []
    for per_author_nodes in authors:
        nodes = strip_whitespace_nodes(per_author_nodes)
        if nodes:
            author_nodes.append(AuthorNode(nodes))

    if author_nodes:
        return [AuthorsNode(author_nodes)]

    return []


def make_metadata_handler(name: str, has_short_bracket=False):
    def handler(parser: ParserCore, token: Token):
        parser.skip_whitespace()
        if has_short_bracket:
            short = parser.parse_bracket_as_nodes()
            parser.skip_whitespace()
        body = parser.parse_brace_as_nodes()
        return [MetadataNode(name, body)]

    return handler


def document_env_handler(parser: ParserCore, token: Token):
    env = parser.parse_environment(token)
    document_node = MetadataNode(NodeTypes.DOCUMENT, env.body)
    document_node.labels = env.labels
    return [document_node]


def abstract_env_handler(parser: ParserCore, token: Token):
    env = parser.parse_environment(token)
    abstract_node = MetadataNode(NodeTypes.ABSTRACT, env.body)
    abstract_node.labels = env.labels
    return [abstract_node]


def appendices_env_handler(parser: ParserCore, token: Token):
    env = parser.parse_environment(token)
    appendix_node = MetadataNode(NodeTypes.APPENDIX, env.body)
    appendix_node.labels = env.labels
    return [appendix_node]


def register_doc_content_handlers(parser: ParserCore):
    # document
    parser.register_env_handler("document", document_env_handler)

    # abstract
    parser.register_env_handler("abstract", abstract_env_handler)
    # \abstract{...} is not native latex, but some packages/classes define \abstract{...} via renewcommand
    parser.register_handler("abstract", make_metadata_handler(NodeTypes.ABSTRACT))

    # title
    parser.register_handler(
        "title", make_metadata_handler(NodeTypes.TITLE, has_short_bracket=True)
    )

    # authors
    parser.register_handler("author", author_handler)
    # \thanks usually found inside author block
    parser.register_handler("thanks", make_metadata_handler("thanks"))

    # address
    parser.register_handler("address", make_metadata_handler(NodeTypes.ADDRESS))
    parser.register_handler("curraddr", lambda parser, token: [])

    # affil
    for affil in ["affiliation", "affil"]:
        parser.register_handler(
            affil, make_metadata_handler(NodeTypes.AFFILIATION, has_short_bracket=True)
        )

    # email
    parser.register_handler("email", make_metadata_handler(NodeTypes.EMAIL))

    # keywords
    parser.register_handler("keywords", make_metadata_handler(NodeTypes.KEYWORDS))

    # appendix
    for appendix in ["appendix", "appendices"]:
        parser.register_handler(
            appendix, lambda parser, token: [MetadataNode(NodeTypes.APPENDIX, [])]
        )

    # \begin{appendix/appendices}
    parser.register_env_handler("appendix", appendices_env_handler)
    parser.register_env_handler("appendices", appendices_env_handler)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
    \title{My Title}
    \address{123 Main St, Anytown, USA}
    \author{John Doe \url{https://example.com} \And some dude \thanks{haha} }
    """.strip()
    out = parser.parse(text)
    print(out)
