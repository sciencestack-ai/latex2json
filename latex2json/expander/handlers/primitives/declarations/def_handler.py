from typing import List, Optional, Tuple
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro, MacroType
from dataclasses import dataclass, field

from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import is_begin_group_token, strip_whitespace_tokens


@dataclass
class DefResult:
    cmd: Token
    definition: List[Token]
    usage_pattern: List[Token]


@dataclass
class PatternSegment:
    is_param: bool = False
    tokens: List[Token] = field(default_factory=list)
    keyword_sequence: Optional[List[str]] = None


def split_usage_pattern_into_segments(
    tokens: List[Token],
) -> List[PatternSegment]:
    segments: List[PatternSegment] = []
    current_group: List[Token] = []

    for tok in tokens:
        if tok.type == TokenType.PARAMETER:
            if current_group:
                segments.append(PatternSegment(is_param=False, tokens=current_group))
                current_group = []
            segments.append(PatternSegment(is_param=True, tokens=[tok]))
        else:
            current_group.append(tok)

    if current_group:
        segments.append(PatternSegment(is_param=False, tokens=current_group))

    for segment in segments:
        if not segment.is_param:
            segment.keyword_sequence = [t.to_str() for t in segment.tokens]

    return segments


def get_parsed_args_from_usage_pattern(
    expander: ExpanderCore, usage_pattern: List[Token]
) -> List[List[Token]]:
    parsed_args: List[List[Token]] = []

    # split usage pattern into segments
    segments = split_usage_pattern_into_segments(usage_pattern)

    N = len(segments)
    i = 0
    while i < N:
        segment = segments[i]

        if not segment.is_param:

            if expander.parse_keyword_sequence(
                segment.keyword_sequence, skip_whitespaces=False
            ):
                i += 1
                continue

            # did not match, return immediately
            raise ValueError(
                f"expected {segment.keyword_sequence} but found {expander.peek()}"
            )
            return parsed_args

        else:
            # segment is param e.g. #1 #2
            # expander.skip_whitespace()
            next_keyword_sequence = None
            if i + 1 < N:
                # check if next segment is a keyword sequence
                # prioritize keyword grabbing/matching
                next_segment = segments[i + 1]
                if not next_segment.is_param:
                    next_keyword_sequence = next_segment.keyword_sequence
                    if expander.parse_keyword_sequence(
                        next_keyword_sequence, skip_whitespaces=False
                    ):
                        i += 2
                        continue

            # parameter matching
            tokens = expander.parse_immediate_token(skip_whitespace=True)
            if tokens is None:
                raise ValueError(f"expected an argument but found nothing")
                return parsed_args

            param_tok = segment.tokens[0]  # must be a parameter token
            index = int(param_tok.value) - 1
            # Extend parsed_args with empty lists if needed
            while len(parsed_args) <= index:
                parsed_args.append([])
            i += 1

            # keep grabbing tokens until next_keyword_sequence is matched
            while next_keyword_sequence and not expander.eof():
                if expander.parse_keyword_sequence(
                    next_keyword_sequence, skip_whitespaces=False
                ):
                    i += 1
                    break
                tok = expander.consume()
                if tok is None or tok.type == TokenType.END_OF_LINE:
                    break
                tokens.append(tok)

            parsed_args[index] = tokens

    return parsed_args


def is_noexpand_token(tok: Token) -> bool:
    return tok.type == TokenType.CONTROL_SEQUENCE and tok.value == "noexpand"


class DefMacro(Macro):
    def __init__(self, name: str, is_lazy=True, is_global=False):
        super().__init__(name)
        self.is_lazy = is_lazy
        self.is_global = is_global

        self.type = MacroType.DECLARATION

        self.handler = lambda expander, node: self._expand(expander, node)

    def _expand(self, expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        expander.skip_whitespace()
        tok = expander.peek()
        # deal with weird case where \noexpand comes right after \def \edef etc. This is only possible if \noexpand is inside an existing \def or \newcommand block etc
        if tok and is_noexpand_token(tok):  # \noexpand
            # return the raw \def token itself since it is inside the definition
            return [token]

        out = def_handler(expander, token)
        if out is None:
            return None

        if not self.is_lazy:
            out.definition = expander.expand_tokens(out.definition)

        def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
            try:
                parsed_args = get_parsed_args_from_usage_pattern(
                    expander, out.usage_pattern
                )
            except ValueError as e:
                expander.logger.info(f"\\def parse args error: {out.cmd}: {e}")
                return []
            subbed = expander.substitute_token_args(out.definition, parsed_args)
            expander.push_tokens(subbed)
            return []

        # Count number of parameters in usage pattern
        num_args = len([t for t in out.usage_pattern if t.type == TokenType.PARAMETER])

        macro = Macro(
            out.cmd,
            handler,
            out.definition,
            num_args=num_args,
            default_arg=None,  # \def doesn't support default args like \newcommand
        )
        expander.register_macro(
            out.cmd, macro, is_global=self.is_global, is_user_defined=True
        )

        return []


def get_def_usage_pattern_and_definition(
    expander: ExpanderCore,
) -> Tuple[List[Token], List[Token]]:
    raw_usage_pattern_tokens = expander.parse_tokens_until(
        lambda tok: is_begin_group_token(tok)
    )
    raw_usage_pattern_tokens = strip_whitespace_tokens(raw_usage_pattern_tokens)

    tok = expander.peek()
    if is_begin_group_token(tok):
        definition_tokens = expander.parse_brace_as_tokens()
        return raw_usage_pattern_tokens, definition_tokens

    return None, None


def def_handler(expander: ExpanderCore, token: Token) -> Optional[DefResult]:
    cmd = expander.parse_command_name_token()
    if not cmd:
        expander.logger.warning(f"\\def expects a control sequence, but found {cmd}")
        return None

    usage_pattern, definition = get_def_usage_pattern_and_definition(expander)

    if usage_pattern is None or definition is None:
        expander.logger.warning(f"\\def expects a proper usage pattern and definition")
        return None

    return DefResult(
        cmd=cmd,
        definition=definition,
        usage_pattern=usage_pattern,
    )


def register_def(expander: ExpanderCore):
    # skip \long
    expander.register_handler("\\long", lambda expander, token: [], is_global=True)

    expander.register_macro(
        "\\def", DefMacro("\\def", is_lazy=True, is_global=False), is_global=True
    )
    for cmd in ["edef", "protected@edef"]:
        expander.register_macro(
            f"\\{cmd}",
            DefMacro(f"\\{cmd}", is_lazy=False, is_global=False),
            is_global=True,
        )
    for cmd in ["gdef", "protected@gdef"]:
        expander.register_macro(
            f"\\{cmd}",
            DefMacro(f"\\{cmd}", is_lazy=True, is_global=True),
            is_global=True,
        )
    for cmd in ["xdef", "protected@xdef"]:
        expander.register_macro(
            f"\\{cmd}",
            DefMacro(f"\\{cmd}", is_lazy=False, is_global=True),
            is_global=True,
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_def(expander)

    # expander.expand(r"\def\foo(e#1{BAR #1 BAR}")

    # text = r"\def\foo(e#1{BAR #1 BAR} \def\hi{HI}"
    # expander.expand(text)

    # out = expander.expand(r"\foo(e\hi")
    # # expected = expander.expand("BAR HI BAR")
    # print(out)

    text = r"""
    \makeatletter
    \def\@parsename#1 #2\end@parsename{%
       1) #1 2) #2 \newline
      \@parsename#2\end@parsename
    }
    \@parsename{AAA} {B CC}\end@parsename
    """.strip()

    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
    # print(expander.expand(r"\bar"))
