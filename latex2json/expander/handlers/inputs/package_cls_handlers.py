from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.types import Token


def usepackage_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    options = expander.parse_bracket_as_tokens(expand=True)
    expander.skip_whitespace()
    packages = expander.parse_brace_name()
    # opt date arg [...]
    expander.skip_whitespace()
    opt_date = expander.parse_bracket_as_tokens(expand=True)
    if not packages:
        expander.logger.warning("No package name provided")
        return None

    packages = [p.strip() for p in packages.split(",")]
    for package in packages:
        expander.load_package(package)

    return []


def replace_package_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    old_package = expander.parse_brace_name()
    expander.skip_whitespace()
    new_package = expander.parse_brace_name()
    if old_package:
        # load old package to register/add to loaded set, but dont read file
        expander.load_package(old_package, read_file=False)
    if new_package:
        expander.load_package(new_package)
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

    # don't ingest documentclass file? i.e. read_file=False
    expander.load_class(cls.strip())  # , read_file=False)

    return []


def make_if_package_cls_handler(command_name: str):
    r"""
    \@ifclasswith{<class>}{<option>}{<true-code>}{<false-code>}
    """

    def if_package_cls_handler(expander: ExpanderCore, token: Token):
        expander.skip_whitespace()
        blocks = expander.parse_braced_blocks(4)
        if len(blocks) != 4:
            expander.logger.warning(f"\\{command_name.lstrip('\\')} expects 4 blocks")
            return None

        true_block = blocks[2]
        false_block = blocks[3]
        # just assume the false block?
        return expander.expand_tokens(false_block)

    return if_package_cls_handler


def register_package_handlers(expander: ExpanderCore):
    # packages
    for cmd_name in ["usepackage", "RequirePackage"]:
        expander.register_handler(
            cmd_name,
            usepackage_handler,
            is_global=True,
        )
    expander.register_handler("ReplacePackage", replace_package_handler, is_global=True)
    # class
    expander.register_handler("documentclass", documentclass_handler, is_global=True)
    expander.register_handler("LoadClass", loadclass_handler, is_global=True)

    # @ifclasswith
    for command_name in ["@ifclasswith", "@ifpackagewith"]:
        expander.register_handler(
            command_name, make_if_package_cls_handler(command_name), is_global=True
        )

    # ignore
    ignore_patterns = {
        "ProvidesClass": "{[",
        "ProvidesPackage": "{[",
        "PassOptionsToClass": 2,
        "PassOptionsToPackage": 2,
    }
    register_ignore_handlers_util(expander, ignore_patterns, expand=True)


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

    text = r"""
        \ReplacePackage{%s/package1.sty}{%s/package2.sty}
    """ % (
        samples_dir,
        samples_dir,
    )

    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out)
