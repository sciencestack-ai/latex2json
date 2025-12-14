from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token
from dataclasses import dataclass
from typing import List, Optional, Dict
from latex2json.registers import RegisterType
from latex2json.expander.handlers.if_else.base_if import IfMacro

from latex2json.tokens.utils import (
    is_comma_token,
    is_equals_token,
    split_tokens_by_predicate,
    strip_whitespace_tokens,
)


@dataclass
class KeyDefinition:
    family: str
    key: str
    definition: List[Token]
    default_tokens: Optional[List[Token]] = None


@dataclass
class BoolKeyDefinition:
    family: str
    key: str
    prefix: str
    default_value: str
    function: List[Token]


def evaluate_bool_key_condition(
    expander: ExpanderCore, token: Token
) -> tuple[bool | None, str | None]:
    """Evaluate the condition for a bool key switch"""
    value = expander.get_register_value(RegisterType.BOOL, token.value)
    if value is None:
        return False, None
    return value, None


class KeyvalManager:
    def __init__(self):
        self.key_definitions: Dict[str, Dict[str, KeyDefinition]] = {}
        self.bool_key_definitions: Dict[str, Dict[str, BoolKeyDefinition]] = {}

    def clear(self):
        self.key_definitions = {}
        self.bool_key_definitions = {}

    def get_key_def(self, fam_name: str, key_name: str) -> Optional[KeyDefinition]:
        if fam_name not in self.key_definitions:
            return None
        if key_name not in self.key_definitions[fam_name]:
            return None
        return self.key_definitions[fam_name][key_name]

    def get_bool_key_def(
        self, fam_name: str, key_name: str
    ) -> Optional[BoolKeyDefinition]:
        if fam_name not in self.bool_key_definitions:
            return None
        if key_name not in self.bool_key_definitions[fam_name]:
            return None
        return self.bool_key_definitions[fam_name][key_name]

    def _create_bool_switch(
        self, expander: ExpanderCore, fam_name: str, key_name: str, prefix: str
    ):
        """Helper method to create and register a Boolean switch"""
        switch_name = f"if{prefix}{key_name}"

        # Register the condition macro
        # Note: If the switch name contains @, it must be used within \makeatletter...\makeatother
        condition = IfMacro(switch_name, evaluate_bool_key_condition)
        expander.register_macro(
            switch_name, condition, is_global=True, is_user_defined=True
        )

        # Initialize the switch to false by default
        expander.set_register(RegisterType.BOOL, switch_name, False, is_global=True)

    def _parse_bool_key_common_args(self, expander: ExpanderCore):
        """Parse common arguments for define@boolkey[s]: +, family, prefix"""
        expander.skip_whitespace()

        # Check for optional + token (allows \par in function body)
        next_token = expander.peek()
        if next_token and next_token.value == "+":
            expander.consume()  # consume the +
            expander.skip_whitespace()

        fam_name = expander.parse_brace_name()
        expander.skip_whitespace()

        # Check for optional prefix in brackets
        prefix_tokens = expander.parse_bracket_as_tokens()
        if prefix_tokens is not None:
            prefix = expander.convert_tokens_to_str(prefix_tokens).strip()
        else:
            # Default prefix is KV@<family>@
            prefix = f"KV@{fam_name}@"

        expander.skip_whitespace()
        return fam_name, prefix

    def define_key(self, expander: ExpanderCore, token: Token):
        expander.skip_whitespace()
        fam_name = expander.parse_brace_name()
        expander.skip_whitespace()
        key_name = expander.parse_brace_name()
        expander.skip_whitespace()
        default_tokens = expander.parse_bracket_as_tokens()
        expander.skip_whitespace()
        tokens = expander.parse_brace_as_tokens()

        if not fam_name:
            expander.logger.warning("No family name provided for define@key")
            return None
        if not key_name:
            expander.logger.warning(f"No key name provided for define@key: {fam_name}")
            return None
        if tokens is None:
            expander.logger.warning(
                f"No tokens provided for define@key: {fam_name}:{key_name}"
            )
            return None

        key_def = KeyDefinition(
            family=fam_name,
            key=key_name,
            definition=tokens,
            default_tokens=default_tokens,
        )

        # Store the key definition
        if fam_name not in self.key_definitions:
            self.key_definitions[fam_name] = {}
        self.key_definitions[fam_name][key_name] = key_def

        return []

    def define_bool_key(self, expander: ExpanderCore, token: Token):
        r"""
        Handles \define@boolkey[+]{family}[prefix]{key}[default]{function}
        Creates a Boolean key with a switch \if<prefix><key>
        The + variant allows \par in the function body (handled automatically)
        """
        # Parse common arguments: +, family, prefix
        fam_name, prefix = self._parse_bool_key_common_args(expander)

        key_name = expander.parse_brace_name()
        expander.skip_whitespace()

        # Check for optional default value in brackets
        default_tokens = expander.parse_bracket_as_tokens()
        if default_tokens is not None:
            default_value = expander.convert_tokens_to_str(default_tokens).strip()
        else:
            default_value = "true"

        expander.skip_whitespace()
        function_tokens = expander.parse_brace_as_tokens()

        if not fam_name:
            expander.logger.warning("No family name provided for define@boolkey")
            return None
        if not key_name:
            expander.logger.warning(
                f"No key name provided for define@boolkey: {fam_name}"
            )
            return None
        if function_tokens is None:
            expander.logger.warning(
                f"No function tokens provided for define@boolkey: {fam_name}:{key_name}"
            )
            return None

        # Store the bool key definition
        bool_key_def = BoolKeyDefinition(
            family=fam_name,
            key=key_name,
            prefix=prefix,
            default_value=default_value,
            function=function_tokens,
        )

        if fam_name not in self.bool_key_definitions:
            self.bool_key_definitions[fam_name] = {}
        self.bool_key_definitions[fam_name][key_name] = bool_key_def

        # Create the switch
        self._create_bool_switch(expander, fam_name, key_name, prefix)

        return []

    def define_bool_keys(self, expander: ExpanderCore, token: Token):
        r"""
        Handles \define@boolkeys[+]{family}[prefix]{key1,key2,key3}[default]
        Creates multiple Boolean keys with the same settings.
        No custom function is permitted (all keys just set their switches).
        """
        # Parse common arguments: +, family, prefix
        fam_name, prefix = self._parse_bool_key_common_args(expander)

        keys_tokens = expander.parse_brace_as_tokens()
        expander.skip_whitespace()

        # Check for optional default value in brackets
        default_tokens = expander.parse_bracket_as_tokens()
        if default_tokens is not None:
            default_value = expander.convert_tokens_to_str(default_tokens).strip()
        else:
            default_value = "true"

        if not fam_name:
            expander.logger.warning("No family name provided for define@boolkeys")
            return None
        if not keys_tokens:
            expander.logger.warning(
                f"No keys provided for define@boolkeys: {fam_name}"
            )
            return None

        # Parse the comma-separated list of keys
        key_items = split_tokens_by_predicate(keys_tokens, is_comma_token)

        for key_item in key_items:
            key_item = strip_whitespace_tokens(key_item)
            if not key_item:
                continue

            key_name = expander.convert_tokens_to_str(key_item).strip()

            # Create a bool key with no custom function (empty list)
            bool_key_def = BoolKeyDefinition(
                family=fam_name,
                key=key_name,
                prefix=prefix,
                default_value=default_value,
                function=[],  # No custom function for bulk definitions
            )

            if fam_name not in self.bool_key_definitions:
                self.bool_key_definitions[fam_name] = {}
            self.bool_key_definitions[fam_name][key_name] = bool_key_def

            # Create the switch
            self._create_bool_switch(expander, fam_name, key_name, prefix)

        return []

    def set_keys(self, expander: ExpanderCore, token: Token):
        expander.skip_whitespace()
        fam_name = expander.parse_brace_name()
        expander.skip_whitespace()
        tokens = expander.parse_brace_as_tokens()

        if not fam_name:
            expander.logger.warning("No family name provided for setkeys")
            return None
        if not tokens:
            expander.logger.warning(f"No keys provided for setkeys: {fam_name}")
            return None

        if (
            fam_name not in self.key_definitions
            and fam_name not in self.bool_key_definitions
        ):
            expander.logger.info(f"Family {fam_name} not defined for setkeys")
            return []

        out_items: List[Token] = []

        key_items = split_tokens_by_predicate(tokens, is_comma_token)
        for item in key_items:
            item = strip_whitespace_tokens(item)
            kv = split_tokens_by_predicate(item, is_equals_token)
            if not kv:
                continue
            key_name = expander.convert_tokens_to_str(kv[0]).strip()

            # Check if it's a bool key first
            bool_key_def = self.get_bool_key_def(fam_name, key_name)
            if bool_key_def:
                # Parse value (default to the default value if not provided)
                if len(kv) > 1:
                    value_str = expander.convert_tokens_to_str(kv[1]).strip()
                    value_tokens = kv[1]
                else:
                    value_str = bool_key_def.default_value
                    # Create tokens from the default value string
                    value_tokens = expander.convert_str_to_tokens(value_str)

                # Set the switch based on the value
                switch_name = f"if{bool_key_def.prefix}{key_name}"
                bool_value = value_str.lower() in ["true", "1", "yes"]
                expander.set_register(
                    RegisterType.BOOL, switch_name, bool_value, is_global=True
                )

                # Execute the custom function if it's not empty
                if bool_key_def.function:
                    out_items.extend(
                        expander.substitute_token_args(
                            bool_key_def.function, [value_tokens]
                        )
                    )
                continue

            # Check if it's a regular key
            key_def = self.get_key_def(fam_name, key_name)
            if not key_def:
                expander.logger.info(f"Key {key_name}, Fam: {fam_name} not defined")
                continue
            value = key_def.default_tokens or []
            if len(kv) > 1:
                value = kv[1]
            definition = key_def.definition
            out_items.extend(expander.substitute_token_args(definition, [value]))

        expander.push_tokens(out_items)

        return []


def register_keyval_handlers(expander: ExpanderCore):
    keyval_manager = KeyvalManager()
    expander.register_handler(r"define@key", keyval_manager.define_key, is_global=True)
    expander.register_handler(
        r"define@boolkey", keyval_manager.define_bool_key, is_global=True
    )
    expander.register_handler(
        r"define@boolkeys", keyval_manager.define_bool_keys, is_global=True
    )
    expander.register_handler(r"setkeys", keyval_manager.set_keys, is_global=True)
    return keyval_manager


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    print("=== Regular key-value pairs ===")
    expander = Expander()
    text = r"""
\def\xxx{XXX}
\makeatletter
\define@key{my}{foo}{Foo is #1 }
\define@key{my}{bar}[99]{Bar is #1 }
\define@key{my}{zac}{Zac is #1 }
\setkeys{my}{foo=\xxx,bar,zac=}
"""
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
    print()

    print("=== Boolean keys ===")
    expander2 = Expander()
    text2 = r"""
\makeatletter
\define@boolkey{opt}{mykey}[true]{Key was set to #1}
\setkeys{opt}{mykey=true}
\ifKV@opt@mykey TRUE\else FALSE\fi

\define@boolkey+{opt}[PREFIX]{verbose}[true]{Verbose: #1}
\setkeys{opt}{verbose}
\ifPREFIXverbose ON\else OFF\fi
"""
    out2 = expander2.expand(text2)
    out2 = strip_whitespace_tokens(out2)
    out_str2 = expander2.convert_tokens_to_str(out2).strip()
    print(out_str2)
    print()

    print("=== Multiple Boolean keys ===")
    expander3 = Expander()
    text3 = r"""
\makeatletter
\define@boolkeys{opt}{debug,verbose,trace}[true]
\setkeys{opt}{debug,verbose=false}
Debug: \ifKV@opt@debug ON\else OFF\fi
Verbose: \ifKV@opt@verbose ON\else OFF\fi
Trace: \ifKV@opt@trace ON\else OFF\fi
"""
    out3 = expander3.expand(text3)
    out3 = strip_whitespace_tokens(out3)
    out_str3 = expander3.convert_tokens_to_str(out3).strip()
    print(out_str3)
