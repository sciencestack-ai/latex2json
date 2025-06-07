import logging
from typing import Dict, List, Optional, Callable
from latex2json.expander.expander import Expander
from latex2json.latex_maps.sections import SECTIONS
from latex2json.nodes import (
    ASTNode,
    EnvironmentNode,
    TextNode,
    EquationNode,
    EquationType,
    SectionNode,
    CommandNode,
    strip_whitespace_nodes,
    merge_text_nodes,
)
from latex2json.nodes.base_nodes import AlignmentNode, NewLineNode
from latex2json.nodes.caption_node import CaptionNode
from latex2json.parser.state import FontStyle, ParserState
from latex2json.tokens import (
    Token,
    CommandWithArgsToken,
    EnvironmentStartToken,
    TokenType,
)

from latex2json.tokens.utils import (
    is_alignment_token,
    is_asterisk_token,
    is_begin_bracket_token,
    is_begin_group_token,
    is_begin_parenthesis_token,
    is_end_bracket_token,
    is_end_group_token,
    is_end_parenthesis_token,
    is_newline_token,
    is_whitespace_token,
)

# Type alias for stop token predicate
TokenPredicate = Callable[[Token], bool]


Handler = Callable[["ParserCore", Token], Optional[List[ASTNode]]]
EnvHandler = Callable[["ParserCore", EnvironmentStartToken], Optional[List[ASTNode]]]


class Macro:
    def __init__(
        self,
        name: str,
        handler: Handler,
    ):
        self.name = name  # usually the command name e.g. \foo
        self.handler = handler


class ParserCore:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.expander = Expander(logger=logger)

        self.token_buffer: List[Token] = []

        self.is_math_mode = False
        self._env_node_stack: List[ASTNode] = []
        self.state = ParserState()

        self.macros: Dict[str, Macro] = {}
        self.env_handlers: Dict[str, EnvHandler] = {}
        self.cite_aliases: Dict[str, str] = {}

    @property
    def current_env(self) -> Optional[ASTNode]:
        return self._env_node_stack[-1] if self._env_node_stack else None

    def set_text(self, text: str):
        self.expander.set_text(text)
        self.token_buffer = []

    def push_tokens(self, tokens: List[Token]):
        """Push tokens to the front of the token buffer."""
        self.token_buffer = tokens + self.token_buffer

    def eof(self) -> bool:
        if not self.token_buffer:
            return self.expander.eof()
        return False

    def peek(self) -> Optional[Token]:
        if self.eof():
            return None
        if not self.token_buffer:
            self.token_buffer = self.expander.next_non_expandable_tokens()
        return self.token_buffer[0] if self.token_buffer else None

    def consume(self) -> Optional[Token]:
        if not self.token_buffer:
            self.peek()
        return self.token_buffer.pop(0) if self.token_buffer else None

    # MACROS (for control sequences/commands)
    def get_macro(self, name: str) -> Optional[Macro]:
        if not name.startswith("\\"):
            name = f"\\{name}"
        return self.macros.get(name)

    def get_all_macros(self) -> Dict[str, Macro]:
        return self.macros.copy()

    def register_macro(self, name: str, macro: Macro):
        if not name.startswith("\\"):
            name = f"\\{name}"
        self.macros[name] = macro

    def register_handler(self, name: str, handler: Handler):
        macro = Macro(name, handler)
        self.register_macro(name, macro)

    # ENVIRONMENTS
    def register_env_handler(self, name: str, handler: EnvHandler):
        self.env_handlers[name] = handler

    def get_env_handler(self, name: str) -> Optional[EnvHandler]:
        return self.env_handlers.get(name)

    def skip_whitespace(self):
        tok = self.peek()
        while tok and is_whitespace_token(tok):
            self.consume()
            tok = self.peek()

    def push_scope(self):
        self.state.push_scope()

    def pop_scope(self):
        self.state.pop_scope()

    def process_tokens(self, tokens: List[Token], scoped=False) -> List[ASTNode]:
        """Parse a list of tokens into AST nodes, similar to expand_tokens in expander."""
        if len(tokens) == 0:
            return []

        if scoped:
            self.push_scope()

        STOP_TOKEN = Token(TokenType.CHARACTER, r"\0", catcode=None)
        self.push_tokens(tokens + [STOP_TOKEN])

        nodes = self.process(
            stop_token_logic=lambda tok: tok is STOP_TOKEN, consume_stop_token=True
        )

        if scoped:
            self.pop_scope()

        return nodes

    def process(
        self,
        stop_token_logic: Optional[TokenPredicate] = None,
        consume_stop_token: bool = True,
    ) -> List[ASTNode]:
        """Process tokens until stop condition is met."""
        nodes: List[ASTNode] = []

        while not self.eof():
            current_token = self.peek()

            if current_token is None:
                break
            if stop_token_logic and stop_token_logic(current_token):
                if consume_stop_token:
                    self.consume()
                break

            parsed_nodes = self.parse_node()
            if parsed_nodes:
                nodes.extend(parsed_nodes)

        return merge_text_nodes(nodes)

    def _handle_font_command(self, cmd_name: str) -> List[ASTNode]:
        if self.expander.state.font_registry.get(cmd_name):
            return []
        return [CommandNode(cmd_name)]

    def set_font(self, style: FontStyle):
        self.state.set_font(style)

    def parse_node(self) -> List[ASTNode]:
        token = self.consume()
        if not token:
            return []

        nodes = self._handler(token)
        if nodes:
            # assign font attributes to nodes
            styles = self.state.get_styles_as_string()
            if styles:
                for node in nodes:
                    node.add_styles(styles, insert_at_front=True)
        return nodes

    def parse(self, text: Optional[str] = None) -> List[ASTNode]:
        if text:
            self.set_text(text)

        return self.process()

    def _handler(self, token: Token) -> List[ASTNode]:
        if token.type == TokenType.CONTROL_SEQUENCE:
            return self.parse_control_sequence(token)
        elif isinstance(token, CommandWithArgsToken):
            return self._handle_command_w_args(token)
        elif isinstance(token, EnvironmentStartToken):
            handler = self.get_env_handler(token.name)
            if handler:
                nodes = handler(self, token)
                return nodes if nodes else []
            env_node = self.parse_environment(token)
            return [env_node]

        if not self.is_math_mode:
            if is_begin_group_token(token):
                self.push_scope()
                return []
            elif is_end_group_token(token):
                self.pop_scope()
                return []

        if is_whitespace_token(token):
            return [TextNode(token.value)]
        elif is_alignment_token(token):
            return [AlignmentNode(token.value)]
        elif token.type == TokenType.CHARACTER:
            return [TextNode(token.value)]
        elif token.type == TokenType.MATH_SHIFT_INLINE:
            return self._handle_math_shift(token, is_inline=True)
        elif token.type == TokenType.MATH_SHIFT_DISPLAY:
            return self._handle_math_shift(token, is_inline=False)
        elif token.type == TokenType.ENVIRONMENT_END:
            return []
        return [TextNode(token.value)]

    def _handle_math_shift(
        self, token: Token, is_inline: bool = True
    ) -> List[EquationNode]:
        self.is_math_mode = True
        math_nodes = self.process(lambda tok: tok == token)
        eq_type = EquationType.INLINE if is_inline else EquationType.DISPLAY
        self.is_math_mode = False
        return [EquationNode(math_nodes, eq_type)]

    def push_env_stack(self, node: ASTNode):
        """Push a node onto the environment stack."""
        self._env_node_stack.append(node)

    def pop_env_stack(
        self, env_node_onwards: Optional[ASTNode] = None
    ) -> Optional[ASTNode]:
        """Pop a node from the environment stack."""
        if not self._env_node_stack:
            return None
        if env_node_onwards:
            # Find target node index and truncate stack if found
            if env_node_onwards in self._env_node_stack:
                idx = self._env_node_stack.index(env_node_onwards)
                self._env_node_stack = self._env_node_stack[:idx]

                return env_node_onwards
        return self._env_node_stack.pop()

    def _generate_env_node(
        self, token: EnvironmentStartToken
    ) -> EnvironmentNode | EquationNode:
        env_name = token.name
        if token.is_math_env:
            eq_type = EquationType.DISPLAY
            if "align" in env_name or "eqnarray" in env_name:
                eq_type = EquationType.ALIGN
            env_node = EquationNode(
                math_nodes=[], numbering=token.numbering, equation_type=eq_type
            )
        else:
            env_node = EnvironmentNode(
                env_name, numbering=token.numbering, display_name=token.display_name
            )
        return env_node

    def parse_environment(
        self, token: EnvironmentStartToken
    ) -> EnvironmentNode | EquationNode:
        env_name = token.name

        env_node = self._generate_env_node(token)
        self.push_env_stack(env_node)

        was_math_mode = self.is_math_mode
        if token.is_math_env:
            self.is_math_mode = True

        begin_predicate: TokenPredicate = (
            lambda tok: tok.type == TokenType.ENVIRONMENT_START
            and tok.value == env_name
        )
        end_predicate: TokenPredicate = (
            lambda tok: tok.type == TokenType.ENVIRONMENT_END and tok.value == env_name
        )
        env_body_nodes = self.parse_begin_end_as_nodes(
            begin_predicate, end_predicate, check_first_token=False, scoped=True
        )
        if isinstance(env_body_nodes, list):
            env_node.set_body(env_body_nodes)
        else:
            self.logger.warning(f"Unmatched environment: {env_name}")

        self.pop_env_stack(env_node)
        self.is_math_mode = was_math_mode
        return env_node

    def parse_control_sequence(self, token: Token) -> List[ASTNode]:
        cmd_name = token.value
        macro = self.get_macro(cmd_name)
        if macro:
            return macro.handler(self, token)

        if is_newline_token(token):
            return [NewLineNode(cmd_name)]
        else:
            if self.expander.state.font_registry.get(cmd_name):
                # ignore defined font commands for now
                # self.set_font(cmd_name)
                return []

        return [CommandNode(cmd_name)]

    def _handle_command_w_args(self, token: CommandWithArgsToken) -> List[ASTNode]:
        if token.name in SECTIONS:
            args = token.args[0]
            opt_args = token.opt_args[0] if token.opt_args else []

            # remove cur env for this section
            self.pop_env_stack()

            arg_nodes = self.process_tokens(args, scoped=True)
            opt_arg_nodes = self.process_tokens(opt_args)
            section_node = SectionNode(
                token.value,
                body=arg_nodes,
                opt_arg=opt_arg_nodes,
                numbering=token.numbering,
            )
            self.push_env_stack(section_node)
            return [section_node]
        elif token.name == "caption":
            args = token.args[0]
            opt_args = token.opt_args[0] if token.opt_args else []

            arg_nodes = self.process_tokens(args, scoped=True)
            opt_arg_nodes = self.process_tokens(opt_args)
            caption_node = CaptionNode(
                body=arg_nodes, opt_arg=opt_arg_nodes, numbering=token.numbering
            )
            self.push_env_stack(caption_node)
            return [caption_node]
        else:
            arg_nodes: List[List[ASTNode]] = []
            opt_arg_nodes: List[List[ASTNode]] = []
            for arg in token.args:
                arg_nodes.append(self.process_tokens(arg, scoped=True))
            for opt_arg in token.opt_args:
                opt_arg_nodes.append(self.process_tokens(opt_arg))
            return [
                CommandNode(
                    token.name,
                    args=arg_nodes,
                    opt_args=opt_arg_nodes,
                    numbering=token.numbering,
                )
            ]

        return []

    def parse_begin_end_as_tokens(
        self,
        begin_predicate: TokenPredicate,
        end_predicate: TokenPredicate,
        check_first_token: bool = True,
        include_begin_end_tokens=False,
    ) -> Optional[List[Token]]:
        """
        Parses a sequence of tokens enclosed in braces '{...}' and returns them as a List[Token].
        The outermost braces are NOT included in the returned list.
        Handles nested braces correctly.

        check_first_token = False is useful if the first token is already consumed and we want to move on
        """
        # 1. Peek at the very first token to check for the opening brace
        first_token = self.peek()

        if not first_token:
            return None

        if check_first_token:
            if not begin_predicate(first_token):
                return None
            self.consume()

        out_tokens: List[Token] = []
        brace_depth = 1  # We've consumed one opening brace, so depth starts at 1

        # 3. Loop until the matching closing brace is found (brace_depth returns to 0)
        while brace_depth > 0:
            current_token = self.peek()

            if current_token is None:
                # Error: Reached the end of the input stream before finding a matching closing brace.
                self.logger.warning(
                    "Unmatched braces: Reached end of stream within a definition."
                )
                # Depending on your error handling strategy, you might raise an exception here
                # or return the partially collected tokens.
                break  # Exit loop due to error

            # Check token type and update brace_depth
            if begin_predicate(current_token):
                brace_depth += 1
            elif end_predicate(current_token):
                brace_depth -= 1

            token = self.consume()
            if token:
                out_tokens.append(token)

        if not include_begin_end_tokens and out_tokens:
            if begin_predicate(out_tokens[0]):
                out_tokens.pop(0)
            if out_tokens and end_predicate(out_tokens[-1]):
                out_tokens.pop()

        return out_tokens

    def parse_begin_end_as_nodes(
        self,
        begin_predicate: TokenPredicate,
        end_predicate: TokenPredicate,
        check_first_token: bool = True,
        include_begin_end_tokens=False,
        scoped=False,
    ) -> Optional[List[ASTNode]]:
        tokens = self.parse_begin_end_as_tokens(
            begin_predicate,
            end_predicate,
            check_first_token=check_first_token,
            include_begin_end_tokens=include_begin_end_tokens,
        )
        if tokens:
            return self.process_tokens(tokens, scoped=scoped)
        return None

    def parse_asterisk(self):
        self.skip_whitespace()
        if is_asterisk_token(self.peek()):
            self.consume()
            return True
        return False

    def parse_brace_as_nodes(self, scoped=False) -> Optional[List[ASTNode]]:
        return self.parse_begin_end_as_nodes(
            is_begin_group_token,
            is_end_group_token,
            include_begin_end_tokens=False,
            scoped=scoped,
        )

    def parse_braced_blocks(self, n_blocks: int) -> Optional[List[ASTNode]]:
        blocks: List[List[ASTNode]] = []
        for _ in range(n_blocks):
            self.skip_whitespace()
            block = self.parse_brace_as_nodes()
            if block is None:
                break
            blocks.append(block)
        return blocks

    def parse_bracket_as_nodes(self, scoped=False) -> Optional[List[ASTNode]]:
        return self.parse_begin_end_as_nodes(
            is_begin_bracket_token,
            is_end_bracket_token,
            include_begin_end_tokens=False,
            scoped=scoped,
        )

    def parse_parenthesis_as_nodes(self) -> Optional[List[ASTNode]]:
        return self.parse_begin_end_as_nodes(
            is_begin_parenthesis_token,
            is_end_parenthesis_token,
            include_begin_end_tokens=False,
            scoped=False,
        )


if __name__ == "__main__":
    parser = ParserCore()

    text = r"""
    \counterwithin{equation}{section}

    \newcounter{myenvx}

    \newenvironment{myenv}[2]{
        \stepcounter{myenvx}
        \renewcommand{\mycmd}[1]{
            \themyenvx: <#1> ##1 <#2>
        }
    }{
        END
    }
    
    \def\html#1{
        \begin{myenv}{html}{/html}
            \mycmd{#1}
        \end{myenv}
    }

    \html{NODE}
    \html{NODE2}

    \section{SECTION}
    \label{sec:section}

""".strip()

    text = r"""
    \textbf{ \textit {NODE} }
    \bf 
    \begin{align}
    1+1
    \end{align}
    """

    parser.set_text(text)
    out = parser.parse()
    out = strip_whitespace_nodes(out)
    print(out)
    # out = parser.expander.expand(text)
