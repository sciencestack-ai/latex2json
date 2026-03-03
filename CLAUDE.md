# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Testing
```bash
pytest tests/
```

## Architecture Overview

This is a Python package that parses LaTeX (.tex) files into structured JSON output, focusing on semantic content extraction rather than visual formatting preservation.

### Core Processing Pipeline

The system follows a multi-stage processing pipeline:

1. **Tokenization** (`latex2json/tokens/`) - Converts raw LaTeX text into tokens with proper catcode handling
2. **Expansion** (`latex2json/expander/`) - Processes macro definitions, expansions, and LaTeX primitives 
3. **Parsing** (`latex2json/parser/`) - Converts expanded tokens into semantic AST nodes
4. **Rendering** (`latex2json/renderer/`) - Transforms AST into final JSON output

### Key Components

#### TexReader (`tex_reader.py`)
- Main entry point for processing LaTeX files/folders/archives
- Handles file extraction and coordinates the processing pipeline
- Returns `ProcessingResult` with tokens and metadata

#### Expander System (`expander/`)
- **ExpanderCore** (`expander_core.py`) - Core macro expansion engine with state management
- **MacroRegistry** (`macro_registry.py`) - Manages macro definitions and handlers
- **Handlers** (`handlers/`) - Specialized processors for different LaTeX constructs:
  - `primitives/` - Basic LaTeX primitives (\def, \let, \newcommand, etc.)
  - `environment/` - Environment handling (\begin{}, \end{}, etc.)
  - `registers/` - Counter and register management
  - `if_else/` - Conditional processing (\if, \else, etc.)
  - `for_loops/` - Loop constructs
  - `text_and_fonts/` - Text formatting and font handling

#### Parser System (`parser/`)
- **ParserCore** (`parser_core.py`) - Converts expanded tokens to semantic AST nodes
- **Handlers** (`handlers/`) - Specialized parsers for different content types:
  - `commands/` - Command processing (references, graphics, etc.)
  - `environments/` - Environment parsing (tables, math, lists, etc.)
  - `bibliography/` - Citation and bibliography handling
- **Bibliography** (`bib/`) - Handles .bib and .bbl file parsing

#### Node System (`nodes/`)
- **BaseNodes** (`base_nodes.py`) - Core AST node types (TextNode, CommandNode, etc.)
- Specialized nodes for sections, equations, tables, captions, environments
- Node utilities for merging and transforming node trees

#### Token System (`tokens/`)
- **Tokenizer** (`tokenizer.py`) - Converts text to tokens with catcode awareness
- **TokenStream** (`token_stream.py`) - Token processing utilities
- **Catcodes** (`catcodes.py`) - LaTeX character category handling

### Processing Modes

The expander supports different processing modes:
- **NORMAL** - Standard LaTeX processing
- **STANDALONE** - Isolated processing for robust parallel execution
- **MATH** - Mathematical content processing

### Key Features

- **Macro Resolution**: Handles complex nested macro definitions with proper scoping
- **Environment Processing**: Supports nested environments including complex table structures
- **Bibliography Support**: Processes citations, .bib files, and bibliography environments  
- **Math Mode**: Comprehensive mathematical expression parsing
- **Package Support**: Extensible package handler system
- **State Management**: Proper scoping for redefined commands and local changes

### Testing Structure

Tests are organized to mirror the main package structure:
- `tests/expander/` - Expander component tests
- `tests/parser/` - Parser component tests  
- `tests/nodes/` - Node system tests
- `tests/tokens/` - Tokenization tests
- `samples/` - Test LaTeX files for integration testing

### Debugging Tips

**Tracing the expander**: Always patch at the CLASS level (`ExpanderCore.method = traced`), never at the instance level (`expander.method = types.MethodType(...)`). Instance patching silently fails due to Python MRO with the `Expander` subclass.

**Token flow**: The parser gets tokens from `expander.next_non_expandable_tokens()` → `expand_next()` → `_exec_macro()`. But `parser.process_tokens()` pushes pre-collected tokens into `parser.token_buffer`, which are consumed WITHOUT re-expansion. If unexpanded macros appear in parser output, check whether they came from the buffer (bypassing expander) or from `expand_next` returning them as non-expandable.

**Scope debugging**: Macros defined with `\def` (is_global=False) are LOCAL to the current scope layer. Trace `ExpanderState.push_scope`/`pop_scope` to find where macros are lost. `\begin{env}` pushes scope; `}` tokens in `expand_next` also push/pop scope.

**`\AtBeginDocument` hooks**: Fire inside `process_environment_begin()` (line ~253), NOT in the fallback path of `begin_environment_handler`. The `force_global_defs` flag on `ExpanderState` ensures definitions inside hooks are global, matching real LaTeX top-level behavior.

**Common macro leak pattern**: If `\@internal@macro` appears literally in equation output, the macro was either (a) never defined, (b) defined locally and lost via scope pop, or (c) defined after the token was already collected. Check `get_macro()` at the point of expansion.

### Important Notes

- The system prioritizes semantic content extraction over visual layout preservation
- Complex drawing environments (tikz, pgfpicture) are preserved as verbatim blocks
- Section numbering may differ from original LaTeX compilation
- Requires Python 3.7+