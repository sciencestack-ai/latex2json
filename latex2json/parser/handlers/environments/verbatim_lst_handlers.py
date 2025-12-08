from latex2json.latex_maps.environments import COMMON_ENVIRONMENTS
from latex2json.nodes.base_nodes import VerbatimNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import (
    EnvironmentStartToken,
    EnvironmentType,
    Token,
    TokenType,
)
from latex2json.utils.encoding import read_file
from latex2json.utils.file_resolver import (
    resolve_file_path,
    get_search_base_from_source,
)


def make_verbatim_handler(env_name: str):
    def verbatim_handler(parser: ParserCore, token: Token):
        tokens = parser.parse_tokens_until(
            lambda tok: tok == Token(TokenType.ENVIRONMENT_END, env_name),
            consume_predicate=True,
        )
        if env_name == "comment":
            # ignore \begin{comment}...
            return []
        return [VerbatimNode(parser.convert_tokens_to_str(tokens).strip())]

    return verbatim_handler


def lstlisting_handler(parser: ParserCore, token: EnvironmentStartToken):
    parser.skip_whitespace()
    title = parser.parse_bracket_as_nodes() or []
    tokens = parser.parse_tokens_until(
        lambda tok: tok == Token(TokenType.ENVIRONMENT_END, "lstlisting"),
        consume_predicate=True,
    )
    if not tokens:
        return []
    return [
        VerbatimNode(
            parser.convert_tokens_to_str(tokens).strip(),
            title=parser.convert_nodes_to_str(title).strip(),
        )
    ]


def minted_handler(parser: ParserCore, token: EnvironmentStartToken):
    parser.skip_whitespace()
    tokens = parser.parse_tokens_until(
        lambda tok: tok == Token(TokenType.ENVIRONMENT_END, "minted"),
        consume_predicate=True,
    )
    if not tokens:
        return []
    title: str | None = None
    if token.args:
        title = parser.convert_tokens_to_str(token.args[0]).strip()
    return [VerbatimNode(parser.convert_tokens_to_str(tokens).strip(), title=title)]


def lstinputlisting_handler(parser: ParserCore, token: Token):
    """Handle \\lstinputlisting[options]{filename} command"""
    parser.skip_whitespace()
    # Parse optional bracket arguments (e.g., [language=Python])
    title_nodes = parser.parse_bracket_as_nodes() or []
    title = parser.convert_nodes_to_str(title_nodes).strip() if title_nodes else None

    parser.skip_whitespace()
    # Parse required brace argument (the filename)
    path_nodes = parser.parse_brace_as_nodes()
    if path_nodes is None:
        parser.logger.warning(r"\lstinputlisting: Missing filename")
        return []

    path_str = parser.convert_nodes_to_str(path_nodes).strip()
    # Strip quotes if present
    path_str = path_str.replace('"', "").replace("'", "")

    # Determine search directory from source file context
    source_file = getattr(token, "source_file", None)
    search_dir = get_search_base_from_source(source_file, parser.project_root, parser.cwd)

    # Resolve file path using the file_resolver utility
    # Don't provide extensions - lstinputlisting requires exact filename
    resolved_path = resolve_file_path(
        path_str,
        cwd=search_dir,
        project_root=parser.project_root,
        extensions=None,
        extra_search_paths=None,
    )

    if resolved_path is None:
        parser.logger.warning(f"\\lstinputlisting: File not found: {path_str}")
        return []

    # Read file content
    try:
        content = read_file(resolved_path)
        if content is None:
            return []
        return [VerbatimNode(content.strip(), title=title)]
    except Exception as e:
        parser.logger.error(f"\\lstinputlisting: Error reading file {resolved_path}: {e}")
        return []


def register_verbatim_lst_handlers(parser: ParserCore):
    for env, env_def in COMMON_ENVIRONMENTS.items():
        if env == "lstlisting":
            parser.register_env_handler(env, lstlisting_handler)
        elif env == "minted":
            parser.register_env_handler(env, minted_handler)
        elif env_def.env_type == EnvironmentType.VERBATIM:
            parser.register_env_handler(env, make_verbatim_handler(env))

    # Register command handlers
    parser.register_handler("lstinputlisting", lstinputlisting_handler)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()
    text = r"""
\begin{minted}[fontsize=\small, bgcolor=gray!10]{javascript}
const x = 10;
\end{minted}
"""
    out = parser.parse(text)
    print(out)
