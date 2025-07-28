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


def loadclass_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    options = expander.parse_bracket_as_tokens(expand=True)
    expander.skip_whitespace()
    classes = expander.parse_brace_name()
    if not classes:
        expander.logger.warning("No class name provided")
        return None

    classes = [p.strip() for p in classes.split(",")]
    for class_name in classes:
        expander.load_class(class_name)

    return []


def documentclass_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    options = expander.parse_bracket_as_tokens(expand=True)
    expander.skip_whitespace()
    cls = expander.parse_brace_name()
    if not cls:
        expander.logger.warning("No class name provided")
        return None

    expander.load_class(cls.strip())

    return []


def endinput_handler(expander: ExpanderCore, token: Token):
    expander.stream.pop_source()
    return []


def register_package_handlers(expander: ExpanderCore):
    # packages
    for cmd_name in ["usepackage", "RequirePackage"]:
        expander.register_handler(
            cmd_name,
            usepackage_handler,
            is_global=True,
        )
    expander.register_handler("endinput", endinput_handler, is_global=True)

    # class
    expander.register_handler("documentclass", documentclass_handler, is_global=True)
    expander.register_handler("LoadClass", loadclass_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander
    import os

    samples_dir = (
        os.path.dirname(os.path.abspath(__file__)) + "/../../../../tests/samples"
    )

    expander = Expander()

    text = r"""

    \documentclass{article}
    \LoadClass{%s/basecls}

    \somecmd
    \begin{document}
    Hello
    \end{document}

    \section{ASDSD}
    """ % (
        samples_dir,
    )

    out = expander.expand(text)
