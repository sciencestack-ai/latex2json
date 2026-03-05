from typing import List, Optional, Dict
from latex2json.expander.expander_core import ExpanderCore, RelaxMacro
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token, TokenType
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


def csappto_handler(expander: ExpanderCore, token: Token):
    r"""
    \csappto{<csname>}{<append>}
    Like \appto but takes a control sequence name (without backslash) instead of a token.
    """
    expander.skip_whitespace()
    csname = expander.parse_brace_name()
    expander.skip_whitespace()
    append = expander.parse_brace_as_tokens()

    if not csname or not append:
        return []

    # Convert csname to command token
    cmd_token = Token(TokenType.CONTROL_SEQUENCE, csname)
    macro = expander.get_macro(cmd_token)
    if not macro:
        return []

    # append to the definition
    macro.definition[:] = macro.definition + append

    return []


def cspreto_handler(expander: ExpanderCore, token: Token):
    r"""
    \cspreto{<csname>}{<prepend>}
    Like \preto but takes a control sequence name (without backslash) instead of a token.
    """
    expander.skip_whitespace()
    csname = expander.parse_brace_name()
    expander.skip_whitespace()
    prepend = expander.parse_brace_as_tokens()

    if not csname or not prepend:
        return []

    # Convert csname to command token
    cmd_token = Token(TokenType.CONTROL_SEQUENCE, csname)
    macro = expander.get_macro(cmd_token)
    if not macro:
        return []

    # prepend to the definition
    macro.definition[:] = prepend + macro.definition

    return []


def ifstrequal_handler(expander: ExpanderCore, token: Token):
    r"""
    Handler for \ifstrequal{string1}{string2}{true-branch}{false-branch}
    Compares two strings and executes the appropriate branch.
    """
    expander.skip_whitespace()

    # Parse the four arguments
    blocks = expander.parse_braced_blocks(4, expand=True, check_immediate_tokens=True)
    if len(blocks) != 4:
        expander.logger.warning("\\ifstrequal expects 4 blocks")
        return []

    str1_tokens = blocks[0]
    str2_tokens = blocks[1]
    true_branch = blocks[2]
    false_branch = blocks[3]

    # Convert tokens to strings for comparison
    str1 = expander.convert_tokens_to_str(str1_tokens).strip()
    str2 = expander.convert_tokens_to_str(str2_tokens).strip()

    # Choose the appropriate branch
    if str1 == str2:
        if true_branch:
            expander.push_tokens(true_branch)
    else:
        if false_branch:
            expander.push_tokens(false_branch)

    return []


def _is_relax_macro(macro: Macro) -> bool:
    """Check if a macro is semantically equivalent to \\relax."""
    if macro is None:
        return False
    return isinstance(macro, RelaxMacro) or (
        len(macro.definition) == 1
        and macro.definition[0].type == TokenType.CONTROL_SEQUENCE
        and macro.definition[0].value == "relax"
    )


def _check_definition(
    expander: ExpanderCore,
    cmd_token: Token,
    true_branch: List[Token],
    false_branch: List[Token],
    treat_relax_as_undefined: bool = False,
):
    """
    Helper function to check if a command is defined and push the appropriate branch.

    Args:
        expander: The expander core instance
        cmd_token: The command token to check
        true_branch: Tokens to push if the condition is true
        false_branch: Tokens to push if the condition is false
        treat_relax_as_undefined: If True, treat \\relax as undefined (for \\ifundef variants)
    """
    macro = expander.get_macro(cmd_token)

    if treat_relax_as_undefined:
        # For \ifundef: undefined if macro doesn't exist OR if it's \relax
        is_undefined = macro is None or _is_relax_macro(macro)
        branch = true_branch if is_undefined else false_branch
    else:
        # For \ifdef: defined if macro exists (including \relax)
        is_defined = macro is not None
        branch = true_branch if is_defined else false_branch

    if branch:
        expander.push_tokens(branch)


def ifdef_handler(expander: ExpanderCore, _token: Token):
    r"""
    Handler for \ifdef{<control sequence>}{<true>}{<false>}
    Expands to <true> if the control sequence is defined, and to <false> otherwise.
    Note that control sequences will be considered as defined even if their meaning is \relax.
    """
    expander.skip_whitespace()
    blocks = expander.parse_braced_blocks(3, expand=False, check_immediate_tokens=True)
    if len(blocks) != 3:
        expander.logger.warning("\\ifdef expects 3 blocks")
        return []

    cmd_tokens, true_branch, false_branch = blocks
    if not cmd_tokens or cmd_tokens[0].type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning("\\ifdef expects a control sequence as first argument")
        if false_branch:
            expander.push_tokens(false_branch)
        return []

    _check_definition(expander, cmd_tokens[0], true_branch, false_branch)
    return []


def ifcsdef_handler(expander: ExpanderCore, _token: Token):
    r"""
    Handler for \ifcsdef{<csname>}{<true>}{<false>}
    Similar to \ifdef except that it takes a control sequence name as its first argument.
    """
    expander.skip_whitespace()
    csname = expander.parse_brace_name()
    if not csname:
        expander.logger.warning("\\ifcsdef expects a control sequence name")
        return []

    expander.skip_whitespace()
    blocks = expander.parse_braced_blocks(2, expand=False, check_immediate_tokens=True)
    if len(blocks) != 2:
        expander.logger.warning("\\ifcsdef expects 3 blocks total")
        return []

    true_branch, false_branch = blocks
    cmd_token = Token(TokenType.CONTROL_SEQUENCE, csname)
    _check_definition(expander, cmd_token, true_branch, false_branch)
    return []


def ifundef_handler(expander: ExpanderCore, _token: Token):
    r"""
    Handler for \ifundef{<control sequence>}{<true>}{<false>}
    Expands to <true> if the control sequence is undefined, and to <false> otherwise.
    Apart from reversing the logic of the test, this command also differs from \ifdef in
    that commands will be considered as undefined if their meaning is \relax.
    """
    expander.skip_whitespace()
    blocks = expander.parse_braced_blocks(3, expand=False, check_immediate_tokens=True)
    if len(blocks) != 3:
        expander.logger.warning("\\ifundef expects 3 blocks")
        return []

    cmd_tokens, true_branch, false_branch = blocks
    if not cmd_tokens or cmd_tokens[0].type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(
            "\\ifundef expects a control sequence as first argument"
        )
        if true_branch:
            expander.push_tokens(true_branch)
        return []

    _check_definition(
        expander,
        cmd_tokens[0],
        true_branch,
        false_branch,
        treat_relax_as_undefined=True,
    )
    return []


def ifcsundef_handler(expander: ExpanderCore, _token: Token):
    r"""
    Handler for \ifcsundef{<csname>}{<true>}{<false>}
    Similar to \ifundef except that it takes a control sequence name as its first argument.
    This command may be used as a drop-in replacement for the \@ifundefined test in the LaTeX kernel.
    """
    expander.skip_whitespace()
    csname = expander.parse_brace_name()
    if not csname:
        expander.logger.warning("\\ifcsundef expects a control sequence name")
        return []

    expander.skip_whitespace()
    blocks = expander.parse_braced_blocks(2, expand=False, check_immediate_tokens=True)
    if len(blocks) != 2:
        expander.logger.warning("\\ifcsundef expects 3 blocks total")
        return []

    true_branch, false_branch = blocks
    cmd_token = Token(TokenType.CONTROL_SEQUENCE, csname)
    _check_definition(
        expander, cmd_token, true_branch, false_branch, treat_relax_as_undefined=True
    )
    return []


def before_begin_environment_handler(expander: ExpanderCore, token: Token):
    r"""
    \BeforeBeginEnvironment{env}{code}
    Registers a hook that runs before \begin{env}.
    """
    expander.skip_whitespace()
    env_name = expander.parse_brace_name()
    if not env_name:
        expander.logger.warning("\\BeforeBeginEnvironment expects an environment name")
        return []

    expander.skip_whitespace()
    hook_tokens = expander.parse_brace_as_tokens(expand=False)
    if hook_tokens is None:
        expander.logger.warning("\\BeforeBeginEnvironment expects code in braces")
        return []

    env_def = expander.get_environment_definition(env_name)
    if not env_def:
        expander.logger.warning(
            f"\\BeforeBeginEnvironment: environment '{env_name}' not found"
        )
        return []

    captured_tokens = hook_tokens

    def before_begin_hook():
        return expander.expand_tokens(list(captured_tokens))

    env_def.hooks.begin.append(before_begin_hook)
    return []


def after_end_environment_handler(expander: ExpanderCore, token: Token):
    r"""
    \AfterEndEnvironment{env}{code}
    Registers a hook that runs after \end{env}.
    """
    expander.skip_whitespace()
    env_name = expander.parse_brace_name()
    if not env_name:
        expander.logger.warning("\\AfterEndEnvironment expects an environment name")
        return []

    expander.skip_whitespace()
    hook_tokens = expander.parse_brace_as_tokens(expand=False)
    if hook_tokens is None:
        expander.logger.warning("\\AfterEndEnvironment expects code in braces")
        return []

    env_def = expander.get_environment_definition(env_name)
    if not env_def:
        expander.logger.warning(
            f"\\AfterEndEnvironment: environment '{env_name}' not found"
        )
        return []

    captured_tokens = hook_tokens

    def after_end_hook():
        return expander.expand_tokens(list(captured_tokens))

    env_def.hooks.end.append(after_end_hook)
    return []


def register_etoolbox_handler(expander: ExpanderCore):
    # Patch commands
    expander.register_handler("patchcmd", patchcmd_macro_handler, is_global=True)
    expander.register_handler("preto", preto_handler, is_global=True)
    expander.register_handler("pretocmd", pretocmd_handler, is_global=True)
    expander.register_handler("appto", appto_handler, is_global=True)
    expander.register_handler("apptocmd", apptocmd_handler, is_global=True)
    expander.register_handler("csappto", csappto_handler, is_global=True)
    expander.register_handler("cspreto", cspreto_handler, is_global=True)

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

    # String comparison
    expander.register_handler("ifstrequal", ifstrequal_handler, is_global=True)

    # Conditional definition checks
    expander.register_handler("ifdef", ifdef_handler, is_global=True)
    expander.register_handler("ifcsdef", ifcsdef_handler, is_global=True)
    expander.register_handler("ifundef", ifundef_handler, is_global=True)
    expander.register_handler("ifcsundef", ifcsundef_handler, is_global=True)

    # Environment hooks
    expander.register_handler(
        "BeforeBeginEnvironment",
        before_begin_environment_handler,
        is_global=True,
    )
    expander.register_handler(
        "AfterEndEnvironment",
        after_end_environment_handler,
        is_global=True,
    )


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
    print()

    # Test ifdef/ifcsdef commands
    ifdef_text = r"""
    \def\definedcmd{value}
    \let\relaxcmd\relax

    \ifdef{\definedcmd}{DEFINED}{UNDEFINED}
    \ifdef{\undefinedcmd}{DEFINED}{UNDEFINED}
    \ifdef{\relaxcmd}{DEFINED}{UNDEFINED}

    \ifcsdef{definedcmd}{DEFINED}{UNDEFINED}
    \ifcsdef{undefinedcmd}{DEFINED}{UNDEFINED}
    \ifcsdef{relaxcmd}{DEFINED}{UNDEFINED}
    """
    ifdef_out = expander.expand(ifdef_text)
    ifdef_str = expander.convert_tokens_to_str(ifdef_out).strip()
    print("ifdef/ifcsdef commands test:")
    print(ifdef_str)
    print()

    # Test ifundef/ifcsundef commands
    ifundef_text = r"""
    \def\definedcmd{value}
    \let\relaxcmd\relax

    \ifundef{\definedcmd}{UNDEFINED}{DEFINED}
    \ifundef{\undefinedcmd}{UNDEFINED}{DEFINED}
    \ifundef{\relaxcmd}{UNDEFINED}{DEFINED}

    \ifcsundef{definedcmd}{UNDEFINED}{DEFINED}
    \ifcsundef{undefinedcmd}{UNDEFINED}{DEFINED}
    \ifcsundef{relaxcmd}{UNDEFINED}{DEFINED}
    """
    ifundef_out = expander.expand(ifundef_text)
    ifundef_str = expander.convert_tokens_to_str(ifundef_out).strip()
    print("ifundef/ifcsundef commands test:")
    print(ifundef_str)
