r"""
expl3 message (msg) handlers.

Handles \msg_new:nnn, \msg_set:nnn, \msg_error:nn, \msg_warning:nn,
\msg_info:nn, and related functions.

Messages are stored in an instance dictionary keyed by (module, message_name).
When a message is issued (error/warning/info), it's consumed silently since
we're parsing LaTeX, not compiling it.
"""

from typing import Dict, List, Optional, Tuple

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


class MsgManager:
    """Manages message storage for expl3 msg commands."""

    def __init__(self):
        self.store: Dict[Tuple[str, str], List[Token]] = {}

    def msg_new_handler(self, expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
        r"""
        \msg_new:nnn {module} {message-name} {message-text}
        Define a new message.
        """
        expander.skip_whitespace()
        module_tokens = expander.parse_brace_as_tokens() or []
        module = "".join(t.value for t in module_tokens).strip()

        expander.skip_whitespace()
        name_tokens = expander.parse_brace_as_tokens() or []
        name = "".join(t.value for t in name_tokens).strip()

        expander.skip_whitespace()
        text_tokens = expander.parse_brace_as_tokens() or []

        if module and name:
            self.store[(module, name)] = text_tokens

        return []

    def msg_new_nnnn_handler(self, expander: ExpanderCore, _token: Token) -> Optional[List[Token]]:
        r"""
        \msg_new:nnnn {module} {message-name} {message-text} {more-text}
        Define a new message with extended text.
        """
        expander.skip_whitespace()
        module_tokens = expander.parse_brace_as_tokens() or []
        module = "".join(t.value for t in module_tokens).strip()

        expander.skip_whitespace()
        name_tokens = expander.parse_brace_as_tokens() or []
        name = "".join(t.value for t in name_tokens).strip()

        expander.skip_whitespace()
        text_tokens = expander.parse_brace_as_tokens() or []

        expander.skip_whitespace()
        more_text_tokens = expander.parse_brace_as_tokens() or []

        if module and name:
            # Combine both text parts
            self.store[(module, name)] = text_tokens + more_text_tokens

        return []

    def msg_if_exist_TF_handler(
        self, expander: ExpanderCore, _token: Token
    ) -> Optional[List[Token]]:
        r"""
        \msg_if_exist:nnTF {module} {message-name} {true} {false}
        Check if a message exists.
        """
        expander.skip_whitespace()
        module_tokens = expander.parse_brace_as_tokens() or []
        module = "".join(t.value for t in module_tokens).strip()

        expander.skip_whitespace()
        name_tokens = expander.parse_brace_as_tokens() or []
        name = "".join(t.value for t in name_tokens).strip()

        expander.skip_whitespace()
        true_branch = expander.parse_brace_as_tokens() or []

        expander.skip_whitespace()
        false_branch = expander.parse_brace_as_tokens() or []

        if (module, name) in self.store:
            expander.push_tokens(true_branch)
        else:
            expander.push_tokens(false_branch)

        return []

    def msg_if_exist_T_handler(
        self, expander: ExpanderCore, _token: Token
    ) -> Optional[List[Token]]:
        r"""
        \msg_if_exist:nnT {module} {message-name} {true}
        """
        expander.skip_whitespace()
        module_tokens = expander.parse_brace_as_tokens() or []
        module = "".join(t.value for t in module_tokens).strip()

        expander.skip_whitespace()
        name_tokens = expander.parse_brace_as_tokens() or []
        name = "".join(t.value for t in name_tokens).strip()

        expander.skip_whitespace()
        true_branch = expander.parse_brace_as_tokens() or []

        if (module, name) in self.store:
            expander.push_tokens(true_branch)

        return []

    def msg_if_exist_F_handler(
        self, expander: ExpanderCore, _token: Token
    ) -> Optional[List[Token]]:
        r"""
        \msg_if_exist:nnF {module} {message-name} {false}
        """
        expander.skip_whitespace()
        module_tokens = expander.parse_brace_as_tokens() or []
        module = "".join(t.value for t in module_tokens).strip()

        expander.skip_whitespace()
        name_tokens = expander.parse_brace_as_tokens() or []
        name = "".join(t.value for t in name_tokens).strip()

        expander.skip_whitespace()
        false_branch = expander.parse_brace_as_tokens() or []

        if (module, name) not in self.store:
            expander.push_tokens(false_branch)

        return []


# Pure functions that don't need instance state (just consume tokens silently)

def _issue_message(
    expander: ExpanderCore, num_args: int = 0
) -> Optional[List[Token]]:
    """
    Helper to consume a message call.
    Parses module name, message name, and optional arguments.
    For our purposes, we just consume the tokens silently.
    """
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # module

    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # name

    # Consume any additional arguments
    for _ in range(num_args):
        expander.skip_whitespace()
        expander.parse_brace_as_tokens()

    return []


def msg_error_nn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \msg_error:nn {module} {message-name}
    Issue an error message (consumed silently).
    """
    return _issue_message(expander, 0)


def msg_error_nnn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \msg_error:nnn {module} {message-name} {arg1}
    Issue an error message with one argument.
    """
    return _issue_message(expander, 1)


def msg_error_nnnn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \msg_error:nnnn {module} {message-name} {arg1} {arg2}
    Issue an error message with two arguments.
    """
    return _issue_message(expander, 2)


def msg_warning_nn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \msg_warning:nn {module} {message-name}
    Issue a warning message (consumed silently).
    """
    return _issue_message(expander, 0)


def msg_warning_nnn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \msg_warning:nnn {module} {message-name} {arg1}
    """
    return _issue_message(expander, 1)


def msg_warning_nnnn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \msg_warning:nnnn {module} {message-name} {arg1} {arg2}
    """
    return _issue_message(expander, 2)


def msg_info_nn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \msg_info:nn {module} {message-name}
    Issue an info message (consumed silently).
    """
    return _issue_message(expander, 0)


def msg_info_nnn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \msg_info:nnn {module} {message-name} {arg1}
    """
    return _issue_message(expander, 1)


def msg_note_nn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \msg_note:nn {module} {message-name}
    Issue a note message (consumed silently).
    """
    return _issue_message(expander, 0)


def msg_note_nnn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \msg_note:nnn {module} {message-name} {arg1}
    """
    return _issue_message(expander, 1)


def msg_log_nn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \msg_log:nn {module} {message-name}
    Log a message (consumed silently).
    """
    return _issue_message(expander, 0)


def msg_none_nn_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \msg_none:nn {module} {message-name}
    Do nothing with the message (consumed silently).
    """
    return _issue_message(expander, 0)


def msg_redirect_name_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \msg_redirect_name:nnn {module} {original} {new}
    Redirect a message to another (consumed silently for now).
    """
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # module
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # original
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # new
    return []


def msg_redirect_class_handler(
    expander: ExpanderCore, _token: Token
) -> Optional[List[Token]]:
    r"""
    \msg_redirect_class:nn {original-class} {new-class}
    Redirect a message class (consumed silently for now).
    """
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # original
    expander.skip_whitespace()
    expander.parse_brace_as_tokens()  # new
    return []


def register_msg_handlers(expander: ExpanderCore) -> None:
    """Register message handlers."""
    # Create instance for this expander
    msg_manager = MsgManager()

    # Creating messages (instance methods)
    for name in ["\\msg_new:nnn", "\\msg_gset:nnn"]:
        expander.register_handler(name, msg_manager.msg_new_handler, is_global=True)
    expander.register_handler("\\msg_set:nnn", msg_manager.msg_new_handler, is_global=True)
    expander.register_handler("\\msg_new:nnnn", msg_manager.msg_new_nnnn_handler, is_global=True)

    # Conditionals (instance methods)
    expander.register_handler("\\msg_if_exist:nnTF", msg_manager.msg_if_exist_TF_handler, is_global=True)
    expander.register_handler("\\msg_if_exist:nnT", msg_manager.msg_if_exist_T_handler, is_global=True)
    expander.register_handler("\\msg_if_exist:nnF", msg_manager.msg_if_exist_F_handler, is_global=True)

    # Pure functions (no state needed - just consume tokens silently)
    # Error messages
    expander.register_handler("\\msg_error:nn", msg_error_nn_handler, is_global=True)
    expander.register_handler("\\msg_error:nnn", msg_error_nnn_handler, is_global=True)
    expander.register_handler("\\msg_error:nnnn", msg_error_nnnn_handler, is_global=True)
    for name in ["\\msg_error:nnx", "\\msg_error:nnxx"]:
        expander.register_handler(name, msg_error_nnn_handler, is_global=True)

    # Warning messages
    expander.register_handler("\\msg_warning:nn", msg_warning_nn_handler, is_global=True)
    expander.register_handler("\\msg_warning:nnn", msg_warning_nnn_handler, is_global=True)
    expander.register_handler("\\msg_warning:nnnn", msg_warning_nnnn_handler, is_global=True)
    for name in ["\\msg_warning:nnx", "\\msg_warning:nnxx"]:
        expander.register_handler(name, msg_warning_nnn_handler, is_global=True)

    # Info messages
    expander.register_handler("\\msg_info:nn", msg_info_nn_handler, is_global=True)
    expander.register_handler("\\msg_info:nnn", msg_info_nnn_handler, is_global=True)

    # Note messages
    expander.register_handler("\\msg_note:nn", msg_note_nn_handler, is_global=True)
    expander.register_handler("\\msg_note:nnn", msg_note_nnn_handler, is_global=True)

    # Log messages
    expander.register_handler("\\msg_log:nn", msg_log_nn_handler, is_global=True)

    # None (silent) messages
    expander.register_handler("\\msg_none:nn", msg_none_nn_handler, is_global=True)

    # Redirects
    expander.register_handler("\\msg_redirect_name:nnn", msg_redirect_name_handler, is_global=True)
    expander.register_handler("\\msg_redirect_class:nn", msg_redirect_class_handler, is_global=True)
