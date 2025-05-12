│   ├── __init__.py          # Imports and potentially re-exports key node classes
│   ├── base.py              # Contains your base ASTNode class
│   ├── syntactic_nodes.py   # Defines fundamental nodes from parsing (CommandNode, TextNode, BraceNode, BracketNode, etc.)
│   ├── definition_nodes.py  # Defines nodes for definition syntax (DefNode, NewCommandNode, LetNode, BaseDefinitionNode, etc.)
│   ├── environment_nodes.py # Defines EnvironmentNode
│   ├── semantic_nodes.py    # Defines higher-level structural nodes created by the expander (SectionNode, ParagraphNode, etc.)
│   ├── table_nodes.py       # Defines nodes specific to tables (TableNode, TableRowNode, TableCellNode, etc.)
│   ├── list_nodes.py        # Defines nodes specific to lists (ListNode, ListItemNode, etc.)
│   ├── math_nodes.py        # Defines nodes for math structures (EquationNode, etc.)
│   ├── csname_node.py       # Defines CsnameNode (if it's a distinct node type)
│   ├── node_stream.py       # Contains the NodeStream utility class (utility for nodes)
│   └── utils.py             # Contains node-related utility functions (utility for nodes)
│