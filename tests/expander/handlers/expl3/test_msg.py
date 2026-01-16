"""Tests for expl3 message (msg) handlers."""

import pytest
from latex2json.expander.expander import Expander
from latex2json.expander.token_processor import TokenProcessor


def to_str(tokens):
    """Helper to convert tokens to string."""
    return TokenProcessor.convert_tokens_to_str(tokens).strip()


class TestMsgNew:
    """Test msg_new:nnn."""

    def setup_method(self):
        self.expander = Expander()

    def test_msg_new_defines_message(self):
        """msg_new:nnn should define a message."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\msg_new:nnn {mymodule} {test-msg} {This is a test message}
\msg_if_exist:nnTF {mymodule} {test-msg} {EXISTS} {NOTEXISTS}
\ExplSyntaxOff
""")
        assert to_str(result) == "EXISTS"

    def test_msg_new_nonexistent_check(self):
        """msg_if_exist:nnTF on undefined message returns false branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\msg_if_exist:nnTF {mymodule} {undefined-msg} {EXISTS} {NOTEXISTS}
\ExplSyntaxOff
""")
        assert to_str(result) == "NOTEXISTS"


class TestMsgSet:
    """Test msg_set:nnn."""

    def setup_method(self):
        self.expander = Expander()

    def test_msg_set_updates_message(self):
        """msg_set:nnn should update or create a message."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\msg_set:nnn {mymodule} {my-msg} {Updated message text}
\msg_if_exist:nnTF {mymodule} {my-msg} {EXISTS} {NOTEXISTS}
\ExplSyntaxOff
""")
        assert to_str(result) == "EXISTS"


class TestMsgError:
    """Test msg_error:nn and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_msg_error_nn_consumed(self):
        """msg_error:nn should be consumed silently."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\msg_error:nn {mymodule} {some-error}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_msg_error_nnn_consumed(self):
        """msg_error:nnn should be consumed silently with one arg."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\msg_error:nnn {mymodule} {some-error} {arg1}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_msg_error_nnnn_consumed(self):
        """msg_error:nnnn should be consumed silently with two args."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\msg_error:nnnn {mymodule} {some-error} {arg1} {arg2}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestMsgWarning:
    """Test msg_warning:nn and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_msg_warning_nn_consumed(self):
        """msg_warning:nn should be consumed silently."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\msg_warning:nn {mymodule} {some-warning}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_msg_warning_nnn_consumed(self):
        """msg_warning:nnn should be consumed silently with one arg."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\msg_warning:nnn {mymodule} {some-warning} {arg1}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestMsgInfo:
    """Test msg_info:nn and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_msg_info_nn_consumed(self):
        """msg_info:nn should be consumed silently."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\msg_info:nn {mymodule} {some-info}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_msg_info_nnn_consumed(self):
        """msg_info:nnn should be consumed silently with one arg."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\msg_info:nnn {mymodule} {some-info} {arg1}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestMsgNote:
    """Test msg_note:nn and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_msg_note_nn_consumed(self):
        """msg_note:nn should be consumed silently."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\msg_note:nn {mymodule} {some-note}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestMsgIfExist:
    """Test msg_if_exist:nnTF and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_msg_if_exist_TF_true(self):
        """msg_if_exist:nnTF on existing message."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\msg_new:nnn {testmod} {testmsg} {text}
\msg_if_exist:nnTF {testmod} {testmsg} {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_msg_if_exist_TF_false(self):
        """msg_if_exist:nnTF on non-existing message."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\msg_if_exist:nnTF {testmod} {nomsg} {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "NO"

    def test_msg_if_exist_T_variant(self):
        """msg_if_exist:nnT only executes true branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\msg_new:nnn {testmod} {testmsg} {text}
X\msg_if_exist:nnT {testmod} {testmsg} {TRUE}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XTRUEY"

    def test_msg_if_exist_T_no_match(self):
        """msg_if_exist:nnT does nothing when message doesn't exist."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\msg_if_exist:nnT {testmod} {nomsg} {TRUE}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_msg_if_exist_F_variant(self):
        """msg_if_exist:nnF only executes false branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\msg_if_exist:nnF {testmod} {nomsg} {FALSE}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XFALSEY"

    def test_msg_if_exist_F_no_execute(self):
        """msg_if_exist:nnF does nothing when message exists."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\msg_new:nnn {testmod} {testmsg} {text}
X\msg_if_exist:nnF {testmod} {testmsg} {FALSE}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestMsgRedirect:
    """Test msg_redirect functions."""

    def setup_method(self):
        self.expander = Expander()

    def test_msg_redirect_name_consumed(self):
        """msg_redirect_name:nnn should be consumed silently."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\msg_redirect_name:nnn {mymodule} {old-msg} {new-msg}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_msg_redirect_class_consumed(self):
        """msg_redirect_class:nn should be consumed silently."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\msg_redirect_class:nn {error} {warning}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestMsgIntegration:
    """Integration tests for message system."""

    def setup_method(self):
        self.expander = Expander()

    def test_multiple_messages(self):
        """Can define and check multiple messages."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\msg_new:nnn {mymod} {msg1} {First message}
\msg_new:nnn {mymod} {msg2} {Second message}
\msg_new:nnn {othermod} {msg1} {Other module message}
\msg_if_exist:nnTF {mymod} {msg1} {1} {0}%
\msg_if_exist:nnTF {mymod} {msg2} {1} {0}%
\msg_if_exist:nnTF {othermod} {msg1} {1} {0}%
\msg_if_exist:nnTF {mymod} {msg3} {1} {0}
\ExplSyntaxOff
""")
        assert to_str(result) == "1110"

    def test_msg_workflow(self):
        """Typical message workflow: define and use."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\msg_new:nnn {mypackage} {invalid-input} {The input #1 is invalid}
\msg_if_exist:nnTF {mypackage} {invalid-input}
  {Message~defined~OK}
  {Message~not~defined}
\ExplSyntaxOff
""")
        assert to_str(result) == "Message~defined~OK"
