from contextvars import Token
from latex2json.nodes import MetadataNode, NodeTypes
from latex2json.nodes.environment_nodes import DocumentNode
from latex2json.parser.handlers.commands.command_handler_utils import (
    register_ignore_handlers_util,
)
from latex2json.parser.parser_core import ParserCore


def make_metadata_handler(name: str, has_short_bracket=False):
    def handler(parser: ParserCore, token: Token):
        parser.skip_whitespace()
        if has_short_bracket:
            short = parser.parse_bracket_as_nodes()
            parser.skip_whitespace()
        body = parser.parse_brace_as_nodes()
        if not body:
            return []
        return [MetadataNode(name, body)]

    return handler


def document_env_handler(parser: ParserCore, token: Token):
    env = parser.parse_environment(token)
    doc_node = DocumentNode(env.body)
    doc_node.labels = env.labels
    return [doc_node]


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

    # other
    for metadata in [
        "keywords",
        "email",
        "affiliation",
        "affil",
        "address",
        "thanks",
        "date",
        "dedicatory",
        "commby",
        "urladdr",
        "subclass",
        "institute",
        "acknowledgments",
        "city",
        "state",
        "country",
        "institution",
        "department",
        "orcid",
        "orcidlink",
        "preprint",
    ]:
        parser.register_handler(
            metadata, make_metadata_handler(metadata, has_short_bracket=True)
        )

    # appendix cmd
    for appendix in ["appendix", "appendices"]:
        parser.register_handler(
            appendix, lambda parser, token: [MetadataNode(NodeTypes.APPENDIX, [])]
        )

    # \begin{appendix/appendices}
    parser.register_env_handler("appendix", appendices_env_handler)
    parser.register_env_handler("appendices", appendices_env_handler)

    ignore_patterns = {
        "theabstract": 0,  # some papers define \theabstract inside \abstract
        # ignore ...running metadata
        "authorrunning": 1,
        "titlerunning": 1,
        # ignore oldschool name + curaddr + addr...
        "name": 0,
        "curaddr": 0,
        "addr": 0,
        "inst": 1,
        "authornotemark": "[",
    }
    register_ignore_handlers_util(parser, ignore_patterns)


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
