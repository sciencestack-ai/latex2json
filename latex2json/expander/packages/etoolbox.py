from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token
from latex2json.tokens.utils import find_token_sequence


def patchcmd_macro_handler(expander: ExpanderCore, token: Token):
    r"""
    \patchcmd{<macro>}{<search>}{<replacement>}{<success>}{<failure>}
    """
    expander.skip_whitespace()
    cmd_token = expander.parse_command_name_token()
    expander.skip_whitespace()
    blocks = expander.parse_braced_blocks(4, expand=False, check_immediate_tokens=True)
    if len(blocks) != 4:
        expander.logger.warning("\\patchcmd expects 5 blocks")
        return None

    search = blocks[0]
    replacement = blocks[1]
    # success = blocks[2]
    # failure = blocks[3]
    macro = expander.get_macro(cmd_token)

    if not macro:
        return []

    # search within definition and replace if exists
    idx = find_token_sequence(macro.definition, search)
    if idx != -1:
        # Replace the found sequence
        new_definition = (
            macro.definition[:idx] + replacement + macro.definition[idx + len(search) :]
        )
        # directly modify the definition in place
        macro.definition[:] = new_definition

    return []


def pretocmd_handler(expander: ExpanderCore, token: Token):
    r"""
    \pretocmd{<macro>}{<prepend>}{<success>}{<failure>}
    """
    expander.skip_whitespace()
    cmd_token = expander.parse_command_name_token()
    expander.skip_whitespace()
    blocks = expander.parse_braced_blocks(3, expand=False, check_immediate_tokens=True)
    if len(blocks) != 3:
        expander.logger.warning("\\pretocmd expects 4 blocks")
        return None

    prepend = blocks[0]
    # success = blocks[1]
    # failure = blocks[2]

    macro = expander.get_macro(cmd_token)
    if not macro:
        return []

    # prepend to the definition
    # prepend to the definition
    macro.definition[:] = prepend + macro.definition

    return []


def apptocmd_handler(expander: ExpanderCore, token: Token):
    r"""
    \apptocmd{<macro>}{<append>}{<success>}{<failure>}
    """
    expander.skip_whitespace()
    cmd_token = expander.parse_command_name_token()
    expander.skip_whitespace()
    blocks = expander.parse_braced_blocks(3, expand=False, check_immediate_tokens=True)
    if len(blocks) != 3:
        expander.logger.warning("\\apptocmd expects 4 blocks")
        return None

    append = blocks[0]
    # success = blocks[1]
    # failure = blocks[2]

    macro = expander.get_macro(cmd_token)
    if not macro:
        return []

    # append to the definition
    macro.definition[:] = macro.definition + append

    return []


def register_etoolbox_handler(expander: ExpanderCore):
    expander.register_handler("patchcmd", patchcmd_macro_handler, is_global=True)
    expander.register_handler("pretocmd", pretocmd_handler, is_global=True)
    expander.register_handler("apptocmd", apptocmd_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    text = r"""
    \makeatletter

    \def\foo{foo}
    \patchcmd{\foo}{o}{ MIDDLE O }{success}{failure}

    \foo % foo -> f MIDDLE O o

    \pretocmd{\foo}{prepend }{success}{failure}
    \foo % f MIDDLE O o -> prepend f MIDDLE O o

    \apptocmd{\foo}{ append}{success}{failure}
    \foo % prepend f MIDDLE O o -> prepend f MIDDLE O o append
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
