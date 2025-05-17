from inspect import stack
from logging import Logger
from typing import Callable, List, Any, Dict, Optional, Type
from typing import List, Optional, Dict, Any, Tuple, Callable, Union, Deque
from collections import deque

from latex2json.expander.macro_registry import (
    Handler,
    Macro,
    MacroRegistry,
)

from latex2json.expander.state import ExpanderState
from latex2json.expander.utils import merge_text_nodes
from latex2json.nodes import (
    ASTNode,
    CommandNode,
    EnvironmentNode,
    TextNode,
    BraceNode,
    ArgNode,
)
from latex2json.nodes.syntactic_nodes import BeginBraceNode, EndBraceNode, EndOfLineNode
from latex2json.parser import ParserCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType


class ExpanderCore:
    """
    The main engine for processing the document.
    Drives parsing, manages state, executes commands, and performs expansion.
    """

    def __init__(
        self, parser: ParserCore = ParserCore(), logger: Logger = Logger("expander")
    ):
        self.parser = parser
        self.state = ExpanderState(parser.tokenizer)  # The stack of state layers
        self.logger = logger

    @property
    def macros(self) -> MacroRegistry:
        return self.state.current.macro_registry

    def register_macro(self, name: str, macro: Macro, is_global: bool = False):
        self.macros.set(name, macro, is_global=is_global)

    def register_handler(self, name: str, handler: Handler, is_global: bool = False):
        self.macros.register_handler(name, handler, is_global=is_global)

    def set_text(self, text: str):
        self.parser.set_text(text)

    def expand(self, text: str) -> List[ASTNode]:
        self.set_text(text)
        return self.process()

    def expand_nodes(self, nodes: List[ASTNode]) -> List[ASTNode]:
        out_nodes: List[ASTNode] = []
        for node in nodes:
            out_nodes.extend(self._process_element(node))
        return merge_text_nodes(out_nodes)

    def push_scope(self):
        self.state.push_scope()

    def pop_scope(self):
        self.state.pop_scope()

    def peek(self) -> Optional[Token]:
        return self.parser.peek()

    def consume(self) -> Optional[Token]:
        return self.parser.consume()

    def skip_whitespace(self):
        return self.parser.skip_whitespace()

    def parse_element(self) -> Optional[List[ASTNode]]:
        element = self.parser.parse_element()
        if element is None:
            return None
        if isinstance(element, CommandNode):
            out = self._handle_command(element)
            return out
        if isinstance(element, BeginBraceNode):
            return [self.parse_brace_group()]
        return [element]

    def parse_brace_group(self) -> BraceNode:
        self.push_scope()  # Correct for runtime scope management for this brace group

        processed_children: List[ASTNode] = []

        # Loop indefinitely until we specifically find the matching EndBraceNode for *this* group.
        # This relies on ExpanderCore.parse_element() recursively handling nested braces
        # by returning full BraceNodes for those inner groups.
        while True:
            # Get the next fully processed element from the Expander's stream.
            # 'nodes' will always be a List[ASTNode] (or None if EOF/error).
            # It will NEVER contain a 'BeginBraceNode' directly, as parse_element converts it
            # into a full BraceNode via recursive call to _handle_brace_group.
            nodes = self.parse_element()

            if nodes is None:
                # In a robust system, you might want to raise a custom exception here (e.g., UnmatchedBraceError)
                break

            # If the first node in the returned list is an EndBraceNode,
            # it means we've found the closing brace for *this* current brace group.
            if len(nodes) > 0 and isinstance(nodes[0], EndBraceNode):
                break  # Exit the loop for this brace group, we're done.

            processed_children.extend(nodes)

        self.pop_scope()  # Pop the scope associated with this brace group
        return BraceNode(processed_children)

    def process(self) -> List[ASTNode]:
        """
        Starts the expansion and processing of the document stream.
        Returns the final list of processed AST nodes.
        """
        final_output_nodes: List[ASTNode] = []

        # The main processing loop
        while not self.parser.eof():
            # Expander pulls the next element from the parser
            next_elements = self.parse_element()

            if next_elements is None:
                # Should only happen at EOF, but handle potential errors
                if not self.parser.eof():
                    print("Error: parse_element returned None before EOF.")
                    break
                break  # Exit loop if parse_element fails or stream is truly empty

            # Process the obtained element (node or potentially raw tokens from expansion queue)
            processed_results = []
            for element in next_elements:
                processed = self._process_element(element)
                if processed:
                    processed_results.extend(processed)

            if processed_results:
                # Add the results of processing to the final output.
                # If expansion inserts tokens/nodes back into the stream,
                # this list might only contain nodes that are not expanded away.
                final_output_nodes.extend(processed_results)

        # After processing, merge consecutive TextNodes in the final output
        # This is a common post-processing step.
        return merge_text_nodes(final_output_nodes)

    def _process_element(self, element: ASTNode) -> Optional[List[ASTNode]]:
        """
        Processes a single AST node obtained from the parser.
        Handles command execution, group processing, etc.
        Returns a list of nodes to be added to the output, or None/empty list
        if the node was fully expanded or handled internally.
        """
        # Check conditional state - skip processing if currently in a false branch
        if not self.state.current.conditional_state.is_true:
            # If skipping, only process nodes that affect conditional state (\else, \fi)
            if isinstance(element, CommandNode):
                if element.name in ["\\else", "\\fi"]:  # Add other conditional commands
                    # Handle the conditional command even when skipping
                    return self._handle_command(element)
            # Skip other nodes when in a false conditional branch
            return []  # Produce no output

        # --- Dispatch based on node type ---

        if isinstance(element, CommandNode):
            # Handle command execution (primitives or macros)
            return self._handle_command(element)

        elif isinstance(element, BeginBraceNode):
            self.push_scope()
            return []

        elif isinstance(element, EndBraceNode):
            self.pop_scope()
            return []

        elif isinstance(element, EndOfLineNode):
            return []  # Produce no output?

        elif isinstance(element, BraceNode):
            # Process the content of a brace group within a new scope
            # The BraceNode was parsed as a block by parser.parse_brace_group
            self.push_scope()  # Start local scope for the group
            # Process the children nodes within this new scope
            processed_children = []
            for child_node in element.children:
                # Recursively process each child node
                results = self._process_element(child_node)
                if results:
                    processed_children.extend(results)
            self.pop_scope()  # End local scope
            # Usually, the BraceNode itself is discarded after processing its content.
            # Return the processed content.
            return processed_children

        elif isinstance(element, EnvironmentNode):
            # Process the content of an environment within a new scope
            # The EnvironmentNode was parsed as a block by parser.parse_environment_syntax
            self.push_scope()  # Start local scope for the environment
            # Environment handling is complex - involves looking up the environment
            # command (e.g., \itemize for itemize environment), executing its handler,
            # which then processes opt_args, args, and body.
            processed_output = self._handle_environment(
                element
            )  # Delegate to environment handler
            self.pop_scope()  # End local scope
            # The environment handler returns the nodes representing the environment's output.
            return processed_output

        elif isinstance(element, ArgNode):
            return [element]
            # return self.expand_nodes(element.value)

        elif isinstance(element, TextNode):
            # Text nodes are typically just passed through to the output
            return [element]

        # --- Handle other node types ---
        # Add handling for MathNode, BracketNode, etc.
        # BracketNode content is often processed by the command handler that uses it.
        # MathNode content needs math parsing after expansion.

        else:
            # Default handling for unknown or unhandled node types - pass them through
            print(
                f"Warning: Unhandled node type: {type(element).__name__}. Passing through."
            )
            return [element]  # Return the node itself

    def _handle_command(self, node: CommandNode) -> Optional[List[ASTNode]]:
        """
        Looks up and executes the command represented by the CommandNode.
        Handles primitive execution and macro expansion.
        Returns a list of nodes to be inserted into the stream/output, or None/empty list.
        """
        command_name = node.name
        definition = self.state.registry.get(
            command_name
        )  # Look up in the current scope's registry

        if definition is None:
            # Undefined command - handle as error
            print(
                f"Error: Undefined command {command_name}."
            )  # Assuming node has position
            # Return the command node itself or an error node for the output
            return [node]

        # --- Execute the command based on its definition type ---

        if definition.handler:
            # Execute the primitive handler function
            # Primitive handlers have access to self (ExpanderCore) and the command node.
            # They are responsible for parsing arguments using self.parser,
            # modifying self.state, and returning any nodes to be inserted/output.
            try:
                # Pass self (the ExpanderCore instance) and the command node to the handler
                return definition.handler(self, node)
            except Exception as e:
                print(f"Error executing primitive {command_name}: {e}")
                # Handle primitive execution errors
                return [node]  # Return the command node on error

        else:
            print(f"Error: No handlers for {command_name}.")
            return [node]  # Return the command node

    def set_catcode(self, char_ord: int, catcode: Catcode):
        self.state.set_catcode(char_ord, catcode)
        self.parser.tokenizer.set_catcode(char_ord, catcode)

    def get_catcode(self, char_ord: int) -> Catcode:
        return self.state.get_catcode(char_ord)


if __name__ == "__main__":
    from latex2json.parser import ParserCore
    from latex2json.tokens.tokenizer import Tokenizer
    from latex2json.tokens.catcodes import Catcode

    expander = ExpanderCore()

    text = r"""
    {
        Outer
        {
            Inner
        }
        Post
    }
    """.strip()
    expander.set_text(text)
    expander.parser.parse_element()
    out = expander.parse_brace_group()
