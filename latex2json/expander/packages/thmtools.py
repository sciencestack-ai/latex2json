from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.environment.environment_utils import is_end_env_token
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.latex_maps.environments import EnvironmentDefinition
from latex2json.tokens.types import EnvironmentType
from typing import Dict, Optional, List

from latex2json.tokens.utils import wrap_tokens_in_braces, wrap_tokens_in_brackets
from latex2json.utils.tex_utils import parse_key_val_string


def declaretheorem_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    options = expander.parse_bracket_as_tokens()
    expander.skip_whitespace()
    env_name = expander.parse_brace_name()
    if not env_name:
        expander.logger.warning(f"\\declaretheorem expects an environment name")
        return None

    options_str = expander.convert_tokens_to_str(options) if options else ""

    parsed_options = parse_key_val_string(options_str)

    display_name = parsed_options.get("name", env_name)
    counter_name = env_name

    numbered = True
    if "numbered" in parsed_options and parsed_options["numbered"] == "no":
        numbered = False

    if numbered:
        if "sibling" in parsed_options:
            counter_name = parsed_options["sibling"]
        elif "sharecounter" in parsed_options:
            counter_name = parsed_options["sharecounter"]
        elif "numberlike" in parsed_options:
            counter_name = parsed_options["numberlike"]
        elif "numberwithin" in parsed_options:
            expander.state.new_counter(counter_name)
            expander.state.counter_within(counter_name, parsed_options["numberwithin"])
        else:
            expander.state.new_counter(counter_name)
    else:
        counter_name = None

    # # Handle Refname (reference name for theorem)
    # if "Refname" in parsed_options:
    #     value = parsed_options["Refname"]

    env_def = EnvironmentDefinition(
        name=env_name,
        display_name=display_name,
        counter_name=counter_name,
        has_direct_command=False,
        env_type=EnvironmentType.THEOREM,
    )
    expander.register_environment(
        env_name, env_def, is_global=True, is_user_defined=True
    )

    return []


def make_restatable_env_def(has_asterisk: bool = False) -> EnvironmentDefinition:
    env_name = "restatable" + ("*" if has_asterisk else "")
    restatable_env_def = EnvironmentDefinition(name=env_name)

    def restatable_env_handler(expander: ExpanderCore, token: Token):
        r"""
        \begin{restatable}[theorem title]{theorem}{csname key}

        e.g. \begin{restatable}[Theorem]{theorem}{MainResult}

        Then later, we can use \MainResult or \MainResult* to reference the theorem title.

        LIMITATION: In real LaTeX, \MainResult* or \begin{restatable*} should reference
        the final numbering of the theorem as it appears in the document (i.e., the number
        from the last occurrence), not produce an unnumbered theorem. However, since our
        expander handles all numbering in the expansion phase (before we know what the
        final number will be), we currently implement the starred version as unnumbered
        (\begin{theorem*}). This is a known limitation of the single-pass architecture.
        """

        def is_restatable_end_token(token: Token) -> bool:
            return is_end_env_token(token, expander, env_name, restatable_env_def)

        expander.skip_whitespace()
        theorem_title = expander.parse_bracket_as_tokens() or []
        expander.skip_whitespace()
        theorem_env_type = expander.parse_brace_as_tokens(
            expand=True
        )  # e.g. theorem, definition, etc
        expander.skip_whitespace()
        cmd_key = expander.parse_brace_name()
        if not theorem_env_type:
            expander.logger.warning(f"\\{env_name} expects a theorem environment type")
            return None
        if not cmd_key:
            expander.logger.warning(f"\\{env_name} expects a key")
            return None

        # parse the env theorem body block, consume_predicate = consume \end token
        theorem_body = expander.parse_tokens_until(
            is_restatable_end_token, verbatim=False, consume_predicate=True
        )
        # consume {restatable} after \end. E.g. \end{restatable}
        expander.parse_brace_name()

        def make_theorem_env_output(has_asterisk: bool = False) -> List[Token]:
            theorem_env_name = theorem_env_type.copy()
            if has_asterisk:
                theorem_env_name.append(
                    Token(TokenType.CHARACTER, "*", catcode=Catcode.OTHER)
                )
            return [
                Token(TokenType.CONTROL_SEQUENCE, "begin"),
                *wrap_tokens_in_braces(theorem_env_name),
                *wrap_tokens_in_brackets(theorem_title),
                *theorem_body,
                Token(TokenType.CONTROL_SEQUENCE, "end"),
                *wrap_tokens_in_braces(theorem_env_name),
                Token(TokenType.END_OF_LINE, "\n"),
            ]

        # push back theorem as regular env # e.g. \begin{theorem_env_type}[theorem_title] theorem_body \end{theorem_env_type}
        expander.push_tokens(make_theorem_env_output(has_asterisk=has_asterisk))

        # additionally, register a macro for the key e.g. \MainResult
        def cmd_key_handler(expander: ExpanderCore, token: Token):
            has_asterisk = expander.parse_asterisk()
            expander.push_tokens(make_theorem_env_output(has_asterisk=has_asterisk))
            return []

        expander.register_macro(
            cmd_key,
            Macro(cmd_key, cmd_key_handler, []),
            is_global=True,
            is_user_defined=True,
        )
        return []

    restatable_env_def.begin_handler = restatable_env_handler

    return restatable_env_def


def register_thmtools(expander: ExpanderCore):
    expander.register_handler("declaretheorem", declaretheorem_handler, is_global=True)

    expander.register_environment(
        "restatable", make_restatable_env_def(has_asterisk=False), is_global=True
    )
    expander.register_environment(
        "restatable*", make_restatable_env_def(has_asterisk=True), is_global=True
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    #     text = r"""
    # \declaretheorem[name=Theorem,Refname={Theorem,Theorems}]{thm}
    # \declaretheorem[name=Definition,Refname={Definition,Definitions},sibling=thm]{defn}

    # \begin{thm} % numbering: 1
    #     This is a theorem
    # \end{thm}

    # \begin{defn} % numbering: 2
    #     This is a definition
    # \end{defn}

    # """.strip()

    text = r"""
    \def\xxx{XXX}
\begin{restatable*}[Sample Property]{theorem}{MainResult}
\label{thm:main} Theorem: \xxx % XXX. real world latex numbering: 2 referencing the latest in the entire document
\end{restatable*}

\def\xxx{YYY}

\MainResult  % \xxx expander to YYY. numbering: 1
\MainResult  % \xxx expander to YYY. numbering: 2
\MainResult* % \xxx expander to YYY. real world latex numbering: 2 referencing the latest in the entire document
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
