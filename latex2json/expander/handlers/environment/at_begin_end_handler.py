from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.types import Token


def make_at_document_hook(expander: ExpanderCore, cmd_name: str, is_begin=True):

    def at_begin_end_document_handler(expander: ExpanderCore, token: Token):
        expander.skip_whitespace()
        tokens = expander.parse_brace_as_tokens(expand=False)

        if tokens is None:
            expander.logger.warning(f"No tokens found in {cmd_name}")
            return None

        doc_env_def = expander.get_environment_definition("document")
        if not doc_env_def:
            expander.logger.warning(f"No document environment found: {cmd_name}")
            return None

        def expand_tokens_hook():
            # In real LaTeX, \AtBeginDocument code runs at the top level (no enclosing group).
            # Force definitions to be global so they persist across scope boundaries.
            old_force = expander.state.force_global_defs
            expander.state.force_global_defs = True
            expander.expand_tokens(tokens)
            expander.state.force_global_defs = old_force
            return []

        hooks = doc_env_def.hooks.begin if is_begin else doc_env_def.hooks.end
        hooks.append(expand_tokens_hook)

        return []

    return at_begin_end_document_handler


def register_at_begin_end_handler(expander: ExpanderCore):
    expander.register_handler(
        "AtBeginDocument",
        make_at_document_hook(expander, "AtBeginDocument", is_begin=True),
        is_global=True,
    )
    expander.register_handler(
        "AtEndDocument",
        make_at_document_hook(expander, "AtEndDocument", is_begin=False),
        is_global=True,
    )

    ignore_patterns = {
        "AtEndOfClass": "{",
    }

    register_ignore_handlers_util(
        expander,
        ignore_patterns,
        expand=True,
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_at_begin_end_handler(expander)

    text = r"""
    \def\aaa{AAA}
    \AtBeginDocument{Hello \aaa}
    \AtBeginDocument{ANOTHER ONE}
    \AtEndDocument{END}

    \def\aaa{BBB}
    
    \begin{document}
    DOC
    \end{document}
    """
    out = expander.expand(text)
    print(out)
