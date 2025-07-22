from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token
from dataclasses import dataclass
from typing import List, Optional, Dict

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


class KeyvalManager:
    def __init__(self):
        self.key_definitions: Dict[str, Dict[str, KeyDefinition]] = {}

    def clear(self):
        self.key_definitions = {}

    def get_key_def(self, fam_name: str, key_name: str) -> Optional[KeyDefinition]:
        if fam_name not in self.key_definitions:
            return None
        if key_name not in self.key_definitions[fam_name]:
            return None
        return self.key_definitions[fam_name][key_name]

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
            expander.logger.warning("No key name provided for define@key")
            return None
        if not tokens:
            expander.logger.warning("No tokens provided for define@key")
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

    def set_keys(self, expander: ExpanderCore, token: Token):
        expander.skip_whitespace()
        fam_name = expander.parse_brace_name()
        expander.skip_whitespace()
        tokens = expander.parse_brace_as_tokens()

        if not fam_name:
            expander.logger.warning("No family name provided for setkeys")
            return None
        if not tokens:
            expander.logger.warning("No keys provided for setkeys")
            return None

        if fam_name not in self.key_definitions:
            expander.logger.info(f"Family {fam_name} not defined for setkeys")
            return []

        out_items: List[Token] = []

        key_items = split_tokens_by_predicate(tokens, is_comma_token)
        for item in key_items:
            item = strip_whitespace_tokens(item)
            kv = split_tokens_by_predicate(item, is_equals_token)
            if not kv:
                continue
            key_name = expander.convert_tokens_to_str(kv[0])
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
    expander.register_handler(r"setkeys", keyval_manager.set_keys, is_global=True)
    return keyval_manager


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

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
