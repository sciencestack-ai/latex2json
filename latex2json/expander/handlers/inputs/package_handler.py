from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def usepackage_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    options = expander.parse_bracket_as_tokens(expand=True)
    expander.skip_whitespace()
    packages = expander.parse_brace_name()
    if not packages:
        expander.logger.warning("No package name provided")
        return None

    packages = [p.strip() for p in packages.split(",")]
    for package in packages:
        expander.load_package(package)

    return []


def register_package_handlers(expander: ExpanderCore):
    expander.register_handler(
        "usepackage",
        usepackage_handler,
        is_global=True,
    )
    expander.register_handler("endinput", lambda expander, token: [], is_global=True)
