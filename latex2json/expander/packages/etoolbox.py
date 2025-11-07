from typing import List, Optional, Dict
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token
from latex2json.tokens.utils import find_token_sequence


class ToggleManager:
    """Manages toggle state for etoolbox toggle commands."""

    def __init__(self):
        self.toggles: Dict[str, bool] = {}

    def create_toggle(self, expander: ExpanderCore, token: Token):
        r"""Handler for \\newtoggle{name}"""
        expander.skip_whitespace()
        name = expander.parse_brace_name()
        if not name:
            expander.logger.warning("\\newtoggle expects a name")
            return []
        self.toggles[name] = False
        return []

    def set_toggle_true(self, expander: ExpanderCore, token: Token):
        r"""Handler for \\toggletrue{name}"""
        expander.skip_whitespace()
        name = expander.parse_brace_name()
        if not name:
            return []
        if name in self.toggles:
            self.toggles[name] = True
        else:
            expander.logger.warning(f"Toggle '{name}' not defined")
        return []

    def set_toggle_false(self, expander: ExpanderCore, token: Token):
        r"""Handler for \\togglefalse{name}"""
        expander.skip_whitespace()
        name = expander.parse_brace_name()
        if not name:
            return []
        if name in self.toggles:
            self.toggles[name] = False
        else:
            expander.logger.warning(f"Toggle '{name}' not defined")
        return []

    def if_toggle(self, expander: ExpanderCore, token: Token):
        r"""Handler for \\iftoggle{name}{true-branch}{false-branch}"""
        expander.skip_whitespace()
        name = expander.parse_brace_name()
        if not name:
            expander.logger.warning("\\iftoggle expects a toggle name")
            return []

        expander.skip_whitespace()
        true_branch = expander.parse_brace_as_tokens(expand=False)
        expander.skip_whitespace()
        false_branch = expander.parse_brace_as_tokens(expand=False)

        # Get toggle state (default to False if not defined)
        is_true = self.toggles.get(name, False)

        # Push the appropriate branch
        branch = true_branch if is_true else false_branch
        if branch:
            expander.push_tokens(branch)

        return []


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


def preto_handler(expander: ExpanderCore, token: Token):
    r"""
    \preto{<macro>}{<prepend>}
    """
    expander.skip_whitespace()
    cmd_token = expander.parse_command_name_token()
    expander.skip_whitespace()
    prepend = expander.parse_brace_as_tokens()

    if not prepend:
        return []

    macro = expander.get_macro(cmd_token)
    if not macro:
        return []

    # prepend to the definition
    macro.definition[:] = prepend + macro.definition

    return []


def pretocmd_handler(expander: ExpanderCore, token: Token):
    r"""
    \pretocmd{<macro>}{<prepend>}{<success>}{<failure>}
    """
    preto_handler(expander, token)
    expander.skip_whitespace()
    # parse additional success/failure blocks
    blocks = expander.parse_braced_blocks(2, expand=False, check_immediate_tokens=True)
    if len(blocks) != 2:
        expander.logger.warning("\\pretocmd expects 4 blocks")
        return None
    return []


def appto_handler(expander: ExpanderCore, token: Token):
    r"""
    \appto{<macro>}{<append>}
    """
    expander.skip_whitespace()
    cmd_token = expander.parse_command_name_token()
    expander.skip_whitespace()
    append = expander.parse_brace_as_tokens()

    if not append:
        return []

    macro = expander.get_macro(cmd_token)
    if not macro:
        return []

    # append to the definition
    macro.definition[:] = macro.definition + append

    return []


def apptocmd_handler(expander: ExpanderCore, token: Token):
    r"""
    \apptocmd{<macro>}{<append>}{<success>}{<failure>}
    """
    appto_handler(expander, token)
    expander.skip_whitespace()
    # parse additional success/failure blocks
    blocks = expander.parse_braced_blocks(2, expand=False, check_immediate_tokens=True)
    if len(blocks) != 2:
        expander.logger.warning("\\apptocmd expects 4 blocks")
        return None
    return []


def register_etoolbox_handler(expander: ExpanderCore):
    # Patch commands
    expander.register_handler("patchcmd", patchcmd_macro_handler, is_global=True)
    expander.register_handler("preto", preto_handler, is_global=True)
    expander.register_handler("pretocmd", pretocmd_handler, is_global=True)
    expander.register_handler("appto", appto_handler, is_global=True)
    expander.register_handler("apptocmd", apptocmd_handler, is_global=True)

    # Toggle commands
    toggle_manager = ToggleManager()
    expander.register_handler("newtoggle", toggle_manager.create_toggle, is_global=True)
    expander.register_handler(
        "toggletrue", toggle_manager.set_toggle_true, is_global=True
    )
    expander.register_handler(
        "togglefalse", toggle_manager.set_toggle_false, is_global=True
    )
    expander.register_handler("iftoggle", toggle_manager.if_toggle, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    # Test patch commands
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
    print("Patch commands test:")
    print(out_str)
    print()

    # Test toggle commands
    toggle_text = r"""
    \newtoggle{mytest}
    \iftoggle{mytest}{TRUE BRANCH}{FALSE BRANCH}

    \toggletrue{mytest}
    \iftoggle{mytest}{TRUE BRANCH}{FALSE BRANCH}

    \togglefalse{mytest}
    \iftoggle{mytest}{TRUE BRANCH}{FALSE BRANCH}
    """
    toggle_out = expander.expand(toggle_text)
    toggle_str = expander.convert_tokens_to_str(toggle_out).strip()
    print("Toggle commands test:")
    print(toggle_str)
