import logging
import os
import re
from collections import deque
from typing import Dict, List, Optional, Callable, Set
from latex2json.expander.expander import Expander
from latex2json.nodes.metadata_nodes import MetadataNode, MaketitleNode
from latex2json.nodes.node_types import NodeTypes
from latex2json.tokens.types import EnvironmentEndToken
from latex2json.expander.state import ProcessingMode
from latex2json.latex_maps.environments import EnvironmentDefinition
from latex2json.latex_maps.sections import SECTIONS
from latex2json.nodes import (
    ASTNode,
    EnvironmentNode,
    TextNode,
    EquationNode,
    DisplayType,
    SectionNode,
    CommandNode,
    AlignmentNode,
    VerbatimNode,
    CaptionNode,
    TheoremNode,
    strip_whitespace_nodes,
    merge_text_nodes,
)
from latex2json.nodes.base_nodes import SpecialCharNode
from latex2json.parser.state import FontStyle, ParserState
from latex2json.tokens import (
    Token,
    CommandWithArgsToken,
    EnvironmentStartToken,
    TokenType,
    EnvironmentType,
    APOSTROPHE_TOKEN,
    BACK_TICK_TOKEN,
)
from latex2json.utils.tex_utils import (
    convert_color_to_css,
    normalize_whitespace_and_lines,
    strip_trailing_whitespace_from_lines,
)

from latex2json.tokens.catcodes import DEFAULT_CATCODES, Catcode
from latex2json.tokens.utils import (
    is_alignment_token,
    is_asterisk_token,
    is_begin_bracket_token,
    is_begin_group_token,
    is_begin_parenthesis_token,
    is_end_bracket_token,
    is_end_group_token,
    is_end_parenthesis_token,
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
        text_mode_only: bool = False,
        math_mode_only: bool = False,
    ):
        self.name = name  # usually the command name e.g. \foo
        self.handler = handler
        self.text_mode_only = text_mode_only
        self.math_mode_only = math_mode_only


class MacroPattern:
    def __init__(
        self,
        name_predicate: Callable[[str], bool],
        handler: Handler,
        text_mode_only: bool = False,
        math_mode_only: bool = False,
    ):
        self.name_predicate = name_predicate
        self.handler = handler
        self.text_mode_only = text_mode_only
        self.math_mode_only = math_mode_only


class ParserCore:
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        expander: Optional[Expander] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.expander = expander or Expander(logger=logger)
        self.standalone_mode: bool = False

        # token buffer
        self.token_buffer: deque[Token] = deque()

        # macros + env handlers
        self.macros: Dict[str, Macro] = {}
        self.macro_patterns: List[MacroPattern] = []
        self.env_handlers: Dict[str, EnvHandler] = {}

        # modes + state
        self._mode_stack: List[ProcessingMode] = [ProcessingMode.TEXT]
        self._env_node_stack: List[ASTNode] = []
        self.state = ParserState()

        # e.g. \defcitealias{sdsds}{Ch 5}
        self.cite_aliases: Dict[str, str] = {}

        # files + external documents + refs resolution
        self.filename: str = ""
        self.external_documents_prefixes: Dict[str, Dict[str, str]] = (
            {}
        )  # file_path -> {filename: prefix}
        self.label_registry: Dict[str, List[str]] = {}  # file_path -> labels

        self.graphics_paths: Set[str] = set()

    def register_label(self, label: str):
        key = self.filename or "default"
        if key not in self.label_registry:
            self.label_registry[key] = []
        self.label_registry[key].append(label)

    def has_label(self, label: str, filename: Optional[str] = None) -> bool:
        key = filename or self.filename or "default"
        if key not in self.label_registry:
            return False
        return label in self.label_registry[key]

    def register_external_document_prefix(self, filename: str, prefix: str):
        key = self.filename
        if not key:
            return
        if key not in self.external_documents_prefixes:
            self.external_documents_prefixes[key] = {}
        self.external_documents_prefixes[key][filename.strip()] = prefix.strip()

    @classmethod
    def create_standalone(
        cls,
        logger: Optional[logging.Logger] = None,
        expander: Optional[Expander] = None,
    ) -> "ParserCore":
        """Create a ParserCore instance for isolated token processing without expander dependency."""
        parser = cls(logger=logger, expander=expander)
        parser.standalone_mode = True
        if expander and expander.cwd:
            parser.cwd = expander.cwd
        return parser

    def push_mode(self, mode: ProcessingMode):
        self._mode_stack.append(mode)

    def pop_mode(self):
        if len(self._mode_stack) <= 1:
            return
        self._mode_stack.pop()

    @property
    def is_math_mode(self) -> bool:
        return self._mode_stack[-1] in [
            ProcessingMode.MATH_INLINE,
            ProcessingMode.MATH_DISPLAY,
        ]

    @property
    def current_env(self) -> Optional[ASTNode]:
        return self._env_node_stack[-1] if self._env_node_stack else None

    @property
    def cwd(self) -> str:
        return self.expander.cwd

    @cwd.setter
    def cwd(self, value: str):
        self.expander.cwd = value

    def get_cwd_path(self, file_path: str) -> str:
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.cwd, file_path)
        return file_path

    def get_colors(self):
        return self.expander.get_colors()

    def clear(self):
        self.expander.clear()
        self.token_buffer.clear()

    def set_text(self, text: str, source_file: Optional[str] = None):
        self.clear()
        self.expander.push_text(text, source_file=source_file)

    def push_tokens(self, tokens: List[Token]):
        """Push tokens to the front of the token buffer."""
        self.token_buffer.extendleft(reversed(tokens))

    def eof(self) -> bool:
        if not self.token_buffer:
            return self.standalone_mode or self.expander.eof()
        return False

    def peek(self) -> Optional[Token]:
        if self.eof():
            return None
        if not self.token_buffer and not self.standalone_mode:
            tokens = self.expander.next_non_expandable_tokens()
            if tokens:
                self.token_buffer.extend(tokens)
        return self.token_buffer[0] if self.token_buffer else None

    def consume(self) -> Optional[Token]:
        if not self.token_buffer:
            self.peek()
        return self.token_buffer.popleft() if self.token_buffer else None

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

    def register_handler(
        self,
        name: str,
        handler: Handler,
        text_mode_only: bool = False,
        math_mode_only: bool = False,
    ):
        macro = Macro(name, handler, text_mode_only, math_mode_only)
        self.register_macro(name, macro)

    def register_macro_pattern(self, macro_pattern: MacroPattern):
        if macro_pattern not in self.macro_patterns:
            self.macro_patterns.append(macro_pattern)

    def register_pattern_handler(
        self,
        name_predicate: Callable[[str], bool],
        handler: Handler,
        text_mode_only: bool = False,
        math_mode_only: bool = False,
    ):
        macro_pattern = MacroPattern(
            name_predicate, handler, text_mode_only, math_mode_only
        )
        self.macro_patterns.append(macro_pattern)

    # ENVIRONMENTS
    def get_environment_definition(
        self, env_name: str
    ) -> Optional[EnvironmentDefinition]:
        return self.expander.get_environment_definition(env_name)

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

    def process_text(self, text: str) -> List[ASTNode]:
        tokens = self.expander.expand_text(text)
        return self.process_tokens(tokens)

    def process_tokens_standalone(self, tokens: List[Token]) -> List[ASTNode]:
        parser = self.create_standalone(logger=self.logger, expander=self.expander)
        return parser.process_tokens(tokens)

    @staticmethod
    def _generate_stop_token():
        return Expander._generate_stop_token()

    def process_tokens(
        self, tokens: List[Token], scoped=False, postprocess=False
    ) -> List[ASTNode]:
        """Parse a list of tokens into AST nodes, similar to expand_tokens in expander."""
        if len(tokens) == 0:
            return []

        if scoped:
            self.push_scope()

        STOP_TOKEN = self._generate_stop_token()

        # number the token positions for logging purposes
        for i, tok in enumerate(tokens):
            tok.position = i
        total_tokens = len(tokens)

        def stop_token_function(tok: Token):
            # log progress...
            if tok.position > 0 and tok.position % 5000 == 0:
                self.logger.info(f"Parsed {tok.position}/{total_tokens} tokens...")
            return tok is STOP_TOKEN

        self.push_tokens(tokens + [STOP_TOKEN])
        nodes = self.process(
            stop_token_logic=stop_token_function, consume_stop_token=True
        )

        if scoped:
            self.pop_scope()

        if postprocess:
            nodes = self.postprocess_nodes(nodes)

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
            for node in nodes:
                if styles:
                    node.add_styles(styles, insert_at_front=True)
                if self.filename and not node.source_file:
                    node.source_file = self.filename
        return nodes

    def parse(
        self,
        text: Optional[str] = None,
        postprocess=False,
        resolve_cross_document_references=False,
        source_file: Optional[str] = None,
    ) -> List[ASTNode]:
        if text:
            self.set_text(text, source_file=source_file)

        out = self.process()
        if postprocess:
            out = self.postprocess_nodes(out)
        if resolve_cross_document_references:
            out = self.resolve_crossdoc_node_refs_labels(out)
        return out

    def parse_file(
        self,
        file_path: str,
        postprocess=False,
        resolve_cross_document_references=False,
        override_cwd=True,
    ) -> Optional[List[ASTNode]]:
        # Resolve file path with extension handling
        resolved_path = self.expander.resolve_file_path(file_path)
        if resolved_path is None:
            self.logger.warning(f"File not found: {file_path}")
            return None

        dir_path = os.path.abspath(os.path.dirname(resolved_path))
        filename = os.path.basename(resolved_path)

        self.filename = filename
        # set expander cwd
        if override_cwd:
            self.cwd = dir_path

        # Read and parse the file content
        content = self.expander.read_file(resolved_path)
        if content is None:
            return None

        # Use the main parse method for consistent behavior
        out = self.parse(
            text=content,
            source_file=resolved_path,
            postprocess=postprocess,
            resolve_cross_document_references=resolve_cross_document_references,
        )

        return out

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
        elif isinstance(token, EnvironmentEndToken):
            # in the wild \end{...}
            self.pop_env_stack(token.value)
            return []

        if is_whitespace_token(token):
            return [TextNode(token.value)]
        elif is_alignment_token(token):
            return [AlignmentNode(token.value)]
        elif token == BACK_TICK_TOKEN:
            char = "'"
            if self.peek() == BACK_TICK_TOKEN:
                self.consume()
                char = '"'
            return [TextNode(char)]
        elif token == APOSTROPHE_TOKEN:
            char = "'"
            if self.peek() == APOSTROPHE_TOKEN:
                self.consume()
                char = '"'
            return [TextNode(char)]
        elif token.type == TokenType.MATH_SHIFT_INLINE:
            return self._handle_math_shift(token, is_inline=True)
        elif token.type == TokenType.MATH_SHIFT_DISPLAY:
            return self._handle_math_shift(token, is_inline=False)
        elif token.type == TokenType.ENVIRONMENT_END:
            return []

        if not self.is_math_mode:
            if is_begin_group_token(token):
                self.push_scope()
                if self.is_in_tabular() or self.is_in_math_mode_stack():
                    # preserve braces as text in math mode stack
                    return [TextNode(token.value)]
                return []
            elif is_end_group_token(token):
                self.pop_scope()
                if self.is_in_tabular() or self.is_in_math_mode_stack():
                    # preserve braces as text in math mode stack
                    return [TextNode(token.value)]
                return []

        return [TextNode(token.value)]

    def _handle_math_shift(
        self, token: Token, is_inline: bool = True
    ) -> List[EquationNode]:
        self.push_mode(
            ProcessingMode.MATH_INLINE if is_inline else ProcessingMode.MATH_DISPLAY
        )
        tok_type = (
            TokenType.MATH_SHIFT_INLINE if is_inline else TokenType.MATH_SHIFT_DISPLAY
        )
        eq_type = DisplayType.INLINE if is_inline else DisplayType.BLOCK
        eq_node = EquationNode(math_nodes=[], equation_type=eq_type)

        self.push_env_stack(eq_node)
        math_nodes = self.process(lambda tok: tok.type == tok_type)
        self.pop_mode()
        self.pop_env_stack(eq_node)
        eq_node.set_body(math_nodes)
        return [eq_node]

    def is_in_env(self, env_name: str) -> bool:
        return any(
            isinstance(node, EnvironmentNode) and node.name == env_name
            for node in self._env_node_stack
        )

    def is_in_tabular(self) -> bool:
        return self.is_in_env("tabular")

    def is_in_math_mode_stack(self) -> bool:
        return any(
            mode in [ProcessingMode.MATH_INLINE, ProcessingMode.MATH_DISPLAY]
            for mode in self._mode_stack
        )

    def push_env_stack(self, node: ASTNode):
        """Push a node onto the environment stack."""
        self._env_node_stack.append(node)

    def pop_env_stack(
        self, env_node_onwards: Optional[ASTNode | str] = None
    ) -> Optional[ASTNode]:
        """Pop a node from the environment stack."""
        if not self._env_node_stack:
            return None
        if isinstance(env_node_onwards, str) and env_node_onwards:
            # Find target node index from the end and truncate stack if found
            for i in range(len(self._env_node_stack) - 1, -1, -1):
                node = self._env_node_stack[i]
                if (
                    isinstance(node, EnvironmentNode)
                    and node.env_name == env_node_onwards
                ):
                    self._env_node_stack = self._env_node_stack[:i]
                    return node
            return None
        elif isinstance(env_node_onwards, ASTNode):
            # Find target node index from the end and truncate stack if found
            for i in range(len(self._env_node_stack) - 1, -1, -1):
                if self._env_node_stack[i] is env_node_onwards:
                    self._env_node_stack = self._env_node_stack[:i]
                    return env_node_onwards
            return None
        return self._env_node_stack.pop()

    def sanitize_string(self, text: str) -> str:
        # convert latex syntax to regular plain text
        # e.g. \textbf{P} -> P
        nodes = self.process_text(text)
        return self.convert_nodes_to_str(nodes)

    def _generate_env_node(
        self, token: EnvironmentStartToken
    ) -> EnvironmentNode | EquationNode:
        env_name = token.name
        numbering = token.numbering
        display_name = token.display_name
        if isinstance(display_name, list):
            # convert tokens to str
            processed_display_name = self.process_tokens(display_name)
            display_name = self.convert_nodes_to_str(processed_display_name)
            if not display_name.strip():
                display_name = env_name
        if numbering:
            # handle cases where numbering is a control sequence e.g. \textbf{P} for e.g. equation \tag{\textbf{P}}
            numbering = self.sanitize_string(numbering)
        if token.env_type in [
            EnvironmentType.EQUATION,
            EnvironmentType.EQUATION_ALIGN,
        ]:
            eq_type = DisplayType.BLOCK
            env_node = EquationNode(
                math_nodes=[],
                numbering=numbering,
                equation_type=eq_type,
                env_name=env_name,
            )
        elif token.env_type == EnvironmentType.THEOREM:
            self.skip_whitespace()
            title_nodes = self.parse_bracket_as_nodes() or []
            title_nodes = self.postprocess_nodes(title_nodes)
            env_node = TheoremNode(
                env_name,
                title=title_nodes,
                numbering=numbering,
                display_name=display_name,
            )
        else:
            env_node = EnvironmentNode(
                env_name, numbering=numbering, display_name=display_name
            )
        return env_node

    def parse_environment(
        self, token: EnvironmentStartToken
    ) -> EnvironmentNode | EquationNode:
        env_name = token.name

        env_node = self._generate_env_node(token)
        self.push_env_stack(env_node)

        is_math = token.env_type in [
            EnvironmentType.EQUATION,
            EnvironmentType.EQUATION_ALIGN,
            EnvironmentType.EQUATION_MATRIX_OR_ARRAY,
        ]

        if is_math:
            self.push_mode(ProcessingMode.MATH_DISPLAY)
        else:
            self.push_mode(ProcessingMode.TEXT)

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
        self.pop_mode()
        return env_node

    def _check_macro_valid(self, macro: Macro | MacroPattern) -> bool:
        valid = True
        in_math_stack = self.is_in_math_mode_stack()
        if macro.text_mode_only and in_math_stack:
            valid = False
        elif macro.math_mode_only and not in_math_stack:
            valid = False
        return valid

    def parse_control_sequence(self, token: Token) -> List[ASTNode]:
        cmd_name = token.value
        macro = self.get_macro(cmd_name)
        if macro and self._check_macro_valid(macro):
            return macro.handler(self, token)

        # check patterns
        for macro_pattern in self.macro_patterns:
            if macro_pattern.name_predicate(cmd_name) and self._check_macro_valid(
                macro_pattern
            ):
                return macro_pattern.handler(self, token)

        if self.expander.state.font_registry.get(cmd_name):
            # ignore defined font commands for now
            # self.set_font(cmd_name)
            return []
        elif cmd_name == "relax":
            return []

        # if not self.is_math_mode and (cmd_name.isalnum() or "@" in cmd_name):
        #     self.logger.info(f"Unknown command: {cmd_name}")
        return [CommandNode(cmd_name)]

    def _handle_command_w_args(self, token: CommandWithArgsToken) -> List[ASTNode]:
        numbering = token.numbering
        if numbering:
            # handle cases where numbering is a control sequence e.g. \textbf{P} for e.g. equation \tag{\textbf{P}}
            numbering = self.sanitize_string(numbering)
        if token.name in SECTIONS:
            args = token.args[0] if token.args else []
            opt_args = token.opt_args[0] if token.opt_args else []

            # remove cur env for this section
            self.pop_env_stack()

            arg_nodes = self.process_tokens(args, scoped=True)
            opt_arg_nodes = self.process_tokens(opt_args)
            label_str = self.convert_nodes_to_str(opt_arg_nodes)
            section_node = SectionNode(
                token.value,
                body=arg_nodes,
                label=label_str,
                numbering=numbering,
            )
            self.push_env_stack(section_node)
            return [section_node]
        elif token.name == "caption":
            args = token.args[0]
            opt_args = token.opt_args[0] if token.opt_args else []

            arg_nodes = self.process_tokens(args, scoped=True)
            opt_arg_nodes = self.process_tokens(opt_args, postprocess=True)
            caption_node = CaptionNode(
                body=arg_nodes,
                opt_arg=opt_arg_nodes,
                numbering=numbering,
                counter_name=token.counter_name,
            )
            self.push_env_stack(caption_node)
            return [caption_node]
        elif token.name in self.expander.state.frontmatter:
            if not token.args:
                return []
            arg_nodes = self.process_tokens(token.args[0])
            node_type = NodeTypes.AUTHOR if token.name == "author" else token.name
            return [MetadataNode(node_type, arg_nodes)]
        elif token.name == "maketitle":
            # Process entire maketitle block standalone to prevent environment boundary issues
            if not token.args:
                return []
            arg_nodes = self.process_tokens_standalone(token.args[0])
            return [MaketitleNode(arg_nodes)]
        elif token.name == "verb":
            verb_tokens = token.args[0]
            verb_text = self.convert_tokens_to_str(verb_tokens)
            return [VerbatimNode(verb_text, display=DisplayType.INLINE)]
        elif token.name == "lstinline":
            verb_tokens = token.args[0]
            verb_text = self.convert_tokens_to_str(verb_tokens)
            title_tokens = token.opt_args[0] if token.opt_args else []
            title_text = self.convert_tokens_to_str(title_tokens)
            return [
                VerbatimNode(verb_text, title=title_text, display=DisplayType.INLINE)
            ]
        elif token.name == "tag":
            # in the wild \tag?
            if isinstance(self.current_env, EquationNode):
                self.current_env.numbering = numbering
            return []
        elif token.name in self.expander.protected_commands:
            arg_nodes: List[List[ASTNode]] = []
            for arg in token.args:
                arg_nodes.append(self.process_tokens(arg, scoped=True))
            if arg_nodes:
                return [MetadataNode(token.name, arg_nodes[0])]
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
                    numbering=numbering,
                )
            ]

        return []

    @staticmethod
    def convert_tokens_to_str(tokens: List[Token]) -> str:
        return Expander.convert_tokens_to_str(tokens)

    def convert_nodes_to_str(self, nodes: List[ASTNode], postprocess=True) -> str:
        if postprocess:
            nodes = self.postprocess_nodes(nodes)
        return "".join(node.detokenize() for node in nodes)

    @staticmethod
    def postprocess_nodes(nodes: List[ASTNode]) -> List[ASTNode]:
        r"""
        post process nodes by
        1. merging spacing, newlines
        2. handling special characters e.g. ~, \& to text
        """
        final_nodes: List[ASTNode] = []

        # parse out all existing stop tokens (shouldn't happen)
        stop_token_value = ParserCore._generate_stop_token().value

        for node in nodes:
            if not node.should_postprocess:
                final_nodes.append(node)
                continue

            replacement_node: Optional[ASTNode] = None

            is_parent_math = node.parent and node.parent.is_math

            if isinstance(node, CommandNode):
                name = node.name
                if name in ["@", stop_token_value]:
                    # \@ -> ""
                    replacement_node = TextNode("")
                elif not is_parent_math:
                    # dont convert these in math nodes
                    if name == "space":
                        replacement_node = TextNode(" ")
                    elif name == "newline":
                        replacement_node = TextNode("\n")
                    elif name == "\\":
                        replacement_node = TextNode("\n")
                    elif (
                        len(name) == 1
                        and DEFAULT_CATCODES.get(ord(name)) != Catcode.LETTER
                    ):
                        # e.g. \& -> &, \# -> #, etc
                        replacement_node = TextNode(name)
            elif isinstance(node, (AlignmentNode, SpecialCharNode)):
                replacement_node = TextNode("")  # empty

            if replacement_node:
                replacement_node.add_styles(node.styles)
                final_nodes.append(replacement_node)
                continue

            if isinstance(node, TextNode):
                if not is_parent_math:
                    text = node.text
                    # collapse multiple spaces into single space (latex)
                    text = normalize_whitespace_and_lines(text)
                    node.text = text.replace("~", " ")
            elif node.children:
                new_children = ParserCore.postprocess_nodes(node.children)
                node.set_children(new_children)

            final_nodes.append(node)

        # mark all as should_postprocess=False
        for node in final_nodes:
            node.should_postprocess = False

        # then do a final merge of text nodes
        merged_nodes = merge_text_nodes(final_nodes)
        # then strip out trailing spaces around newlines
        for node in merged_nodes:
            if isinstance(node, TextNode):
                node.text = strip_trailing_whitespace_from_lines(node.text)

        return merged_nodes

    def resolve_crossdoc_node_refs_labels(self, nodes: List[ASTNode]):
        from latex2json.parser.references.reference_resolver import (
            generate_reference_registries,
            resolve_node_references_and_labels,
        )

        # if external documents are defined, resolve references and labels for cross document nodes
        if len(self.external_documents_prefixes) > 0:
            self.logger.info(
                "Resolving references and labels for cross document nodes..."
            )
            reference_registries = generate_reference_registries(self)
            resolve_node_references_and_labels(
                nodes, reference_registries, recurse=True
            )
        return nodes

    def parse_tokens_until(
        self, predicate: TokenPredicate, consume_predicate=False
    ) -> List[Token]:
        tokens = []
        while not self.eof():
            tok = self.peek()
            if predicate(tok):
                if consume_predicate:
                    self.consume()
                return tokens
            tokens.append(self.consume())
        return tokens

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

        out_tokens: List[Token] = []

        if check_first_token:
            if not begin_predicate(first_token):
                return None
            begin_token = self.consume()
            out_tokens.append(begin_token)

        brace_depth = 1  # We've consumed one opening brace, so depth starts at 1

        # 3. Loop until the matching closing brace is found (brace_depth returns to 0)
        while brace_depth > 0 and not self.eof():
            current_token = self.peek()

            if current_token is None:
                # Error: Reached the end of the input stream before finding a matching closing brace.
                self.logger.info(
                    "Parser - Unmatched braces: Reached end of stream within a definition."
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
        if tokens is not None:
            return self.process_tokens(tokens, scoped=scoped)
        return None

    def parse_asterisk(self):
        self.skip_whitespace()
        if is_asterisk_token(self.peek()):
            self.consume()
            return True
        return False

    def parse_brace_as_nodes(self, scoped=True) -> Optional[List[ASTNode]]:
        return self.parse_begin_end_as_nodes(
            is_begin_group_token,
            is_end_group_token,
            include_begin_end_tokens=False,
            scoped=scoped,
        )

    def parse_brace_name(self) -> Optional[str]:
        nodes = self.parse_brace_as_nodes(scoped=False)
        if nodes:
            return self.convert_nodes_to_str(nodes)
        return None

    def parse_braced_blocks(self, n_blocks: int) -> Optional[List[List[ASTNode]]]:
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

    def parse_immediate_node(
        self, scoped: bool = False, skip_whitespace: bool = False
    ) -> Optional[List[ASTNode]]:
        """Parse either a braced group or a single token as nodes.

        Args:
            scoped: If True, process tokens in a new scope
            skip_whitespace: If True, skip whitespace before parsing

        Returns:
            List of ASTNodes, or None if no token available
        """
        if skip_whitespace:
            self.skip_whitespace()

        tok = self.peek()
        if not tok:
            return None

        if is_begin_group_token(tok):
            return self.parse_brace_as_nodes(scoped=scoped)
        else:
            consumed = self.consume()
            if consumed:
                return self._handler(consumed)
            return None

    def parse_color_name(self) -> Optional[str]:
        r"""\s*[model]\s*{color_name}"""
        self.skip_whitespace()
        model_color_nodes = self.parse_bracket_as_nodes()
        self.skip_whitespace()
        color_name_nodes = self.parse_brace_as_nodes(scoped=False)
        if not color_name_nodes:
            return None

        color_name = self.convert_nodes_to_str(color_name_nodes)
        if model_color_nodes:
            model_str = self.convert_nodes_to_str(model_color_nodes)
            color_name = convert_color_to_css(model_str, color_name)

        return color_name


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
    `single quote' ``double quote''
    """

    parser.set_text(text)
    out = parser.parse()
    out = strip_whitespace_nodes(out)
    print(out)
    # out = parser.expander.expand(text)
