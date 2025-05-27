import logging
from typing import List, Optional, Callable
from latex2json.expander.expander import Expander
from latex2json.latex_maps.sections import SECTIONS
from latex2json.nodes.environment_nodes import EnvironmentNode
from latex2json.nodes.math_nodes import EquationNode, EquationType
from latex2json.nodes.semantic_nodes import SectionNode
from latex2json.nodes.syntactic_nodes import CommandNode, strip_whitespace_nodes
from latex2json.tokens import Token
from latex2json.tokens.types import (
    CommandWithArgsToken,
    EnvironmentStartToken,
    TokenType,
)

from latex2json.nodes import ASTNode, TextNode
from latex2json.nodes.utils import merge_text_nodes
from latex2json.tokens.utils import (
    is_begin_bracket_token,
    is_begin_group_token,
    is_end_bracket_token,
    is_end_group_token,
    is_whitespace_token,
)

# Type alias for stop token predicate
TokenPredicate = Callable[[Token], bool]


class Parser:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.expander = Expander(logger=logger)

        self.token_buffer: List[Token] = []

        self.is_math_mode = False
        self._env_node_stack: List[EnvironmentNode] = []

    @property
    def current_env(self) -> Optional[EnvironmentNode]:
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

    def skip_whitespace(self):
        tok = self.peek()
        while tok and is_whitespace_token(tok):
            self.consume()
            tok = self.peek()

    def push_scope(self):
        pass

    def pop_scope(self):
        pass

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

    def parse_node(self) -> List[ASTNode]:
        token = self.consume()
        if not token:
            return []

        return self._handler(token)

    def parse(self, text: Optional[str] = None) -> List[ASTNode]:
        if text:
            self.set_text(text)

        return self.process()

    def _handler(self, token: Token) -> List[ASTNode]:
        if not self.is_math_mode:
            if is_begin_group_token(token):
                self.push_scope()
                return []
            elif is_end_group_token(token):
                self.pop_scope()
                return []

        if is_whitespace_token(token):
            return [TextNode(token.value)]
        elif token.type == TokenType.CHARACTER:
            return [TextNode(token.value)]
        elif token.type == TokenType.MATH_SHIFT_INLINE:
            return self._handle_math_shift(token, is_inline=True)
        elif token.type == TokenType.MATH_SHIFT_DISPLAY:
            return self._handle_math_shift(token, is_inline=False)
        elif isinstance(token, EnvironmentStartToken):
            return self._handle_environment(token)
        elif token.type == TokenType.ENVIRONMENT_END:
            return []
        elif token.type == TokenType.CONTROL_SEQUENCE:
            return self._handle_control_sequence(token)
        elif isinstance(token, CommandWithArgsToken):
            return self._handle_command_w_args(token)
        return [TextNode(token.value)]

    def _handle_math_shift(
        self, token: Token, is_inline: bool = True
    ) -> List[EquationNode]:
        self.is_math_mode = True
        math_nodes = self.process(lambda tok: tok == token)
        eq_type = EquationType.INLINE if is_inline else EquationType.DISPLAY
        self.is_math_mode = False
        return [EquationNode(math_nodes, eq_type)]

    def push_env_stack(self, node: EnvironmentNode):
        """Push a node onto the environment stack."""
        self._env_node_stack.append(node)

    def pop_env_stack(self) -> Optional[EnvironmentNode]:
        """Pop a node from the environment stack."""
        return self._env_node_stack.pop() if self._env_node_stack else None

    def _handle_environment(self, token: EnvironmentStartToken) -> List[ASTNode]:
        env_name = token.name

        env_node = EnvironmentNode(env_name, numbering=token.numbering)
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

        self.pop_env_stack()
        self.is_math_mode = was_math_mode
        return [env_node]

    @staticmethod
    def convert_nodes_to_str(nodes: List[ASTNode]) -> str:
        return "".join(node.detokenize() for node in nodes)

    def _handle_control_sequence(self, token: Token) -> List[ASTNode]:
        # TODO: HANDLERS
        if token.value == "label":
            self.skip_whitespace()
            label_value = self.parse_brace_as_nodes()
            label_str = self.convert_nodes_to_str(label_value)
            env_node = self.current_env
            if env_node:
                env_node.labels.append(label_str)
            return []
        return [CommandNode(token.value)]

    def _handle_command_w_args(self, token: CommandWithArgsToken) -> List[ASTNode]:
        if token.name in SECTIONS:
            args = token.args[0]
            opt_args = token.opt_args[0] if token.opt_args else []

            # remove cur env for this section
            self.pop_env_stack()

            args_ast = self.process_tokens(args, scoped=True)
            opt_args_ast = self.process_tokens(opt_args)
            section_node = SectionNode(
                token.value,
                body=args_ast,
                opt_arg=opt_args_ast,
                numbering=token.numbering,
            )
            self.push_env_stack(section_node)
            return [section_node]

        return []

    def _parse_begin_end_as_tokens(
        self,
        begin_predicate: TokenPredicate,
        end_predicate: TokenPredicate,
        check_first_token: bool = True,
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

        return out_tokens

    def parse_begin_end_as_nodes(
        self,
        begin_predicate: TokenPredicate,
        end_predicate: TokenPredicate,
        check_first_token: bool = True,
        scoped=False,
    ) -> Optional[List[ASTNode]]:
        tokens = self._parse_begin_end_as_tokens(
            begin_predicate, end_predicate, check_first_token
        )
        if tokens:
            return self.process_tokens(tokens, scoped=scoped)
        return None

    def parse_brace_as_nodes(self, scoped=False) -> Optional[List[ASTNode]]:
        return self.parse_begin_end_as_nodes(
            is_begin_group_token, is_end_group_token, scoped=scoped
        )

    def parse_bracket_as_nodes(self, scoped=False) -> Optional[List[ASTNode]]:
        return self.parse_begin_end_as_nodes(
            is_begin_bracket_token, is_end_bracket_token, scoped=scoped
        )


if __name__ == "__main__":
    parser = Parser()

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
    \let\pminus\pm
    \renewcommand{\pm}{\phi_{\le m}}
    \let\postpm\pm

    \newcommand{\abs}[1]{\left\vert#1\right\vert}
    \newcommand{\ti}{\tilde}
    \newcommand{\calR}{\mathcal R}
    \newcommand{\gab}{g^{\alpha\beta}}
    \newcommand{\paa}{\partial_\alpha}
    \newcommand{\f}{\frac}
    \newcommand{\la}{\left\vert}

    $\abs{x}$ % \left\vert{x}\right\vert
    $\ti{3}$ % $\tilde{3}$
    $\frac\calR 2$ % $\frac{\mathcal R} 2$
    $\paa\gab$ % \partial_\alpha{g^{\alpha\beta}}
    $\Delta^\paa$ % \Delta^\partial_\alpha
    $x^\f{1}{2}$ % x^\frac{1}{2}
    $\la \nabla_{x,y}$ % \left\vert \nabla_{x,y}
    $\chi(x-x_0) \la$ % \chi(x-x_0) \left\vert
    $\pminus$ % \pm
    $\postpm$ % \phi_{\le m}
    """

    parser.set_text(text)
    out = parser.parse()
    out = strip_whitespace_nodes(out)
    print(out)
    # out = parser.expander.expand(text)
