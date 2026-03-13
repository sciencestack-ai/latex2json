# LaTeX2JSON

A fast and robust LaTeX-to-JSON parser in pure python (no TeX installations). [Tested on 500k+ arXiv papers.](#tested-on-500000-arxiv-papers) Extract sections, equations, figures, citations, and metadata from LaTeX into typed JSON.

## Why LaTeX2JSON?

We needed to parse hundreds of thousands of real arXiv papers into structured data. Outside of full LaTeX engines, existing LaTeX conversion tools like Pandoc do not handle complex real world LaTeX. None of them produce a clean JSON AST from arbitrary papers that could also handle custom macros and bundled style files.

LaTeX2JSON focuses specifically on this problem: **reliably extracting semantic structure from real-world LaTeX into JSON**.

- **Pure Python** — No TeX installation required. Runs anywhere Python runs.
- **Macro expansion** — Resolves `\newcommand`, `\def`, `\let`, `\renewcommand`, `\csname`, nested definitions, starred variants, optional arguments
- **Scoping** — Tracks scope correctly when macros are redefined mid-document
- **Style files** — Parses real-world `.sty` and `.cls` files, expanding the macro definitions they provide
- **expl3** — Partial support for LaTeX3 programming layer (22 modules)

Every token is typed with a `type` field (`section`, `equation`, `figure`, `citation`, ...) and carries its metadata — numbering, display mode, nesting depth. The output is a tree you can walk, filter, and query:

```python
from latex2json import TexReader
import json

reader = TexReader()
result = reader.process("paper.tar.gz")
tokens = json.loads(reader.to_json(result))

# pull all block equations from the paper
def walk(nodes):
    for node in nodes:
        if node.get("type") == "equation" and node.get("display") == "block":
            yield node
        yield from walk(node.get("content", []) if isinstance(node.get("content"), list) else [])

equations = list(walk(tokens))
# [{"type": "equation", "display": "block", "numbering": "1", "content": [...]}, ...]
```

## Table of Contents

- [Quick Start](#quick-start)
- [Output Structure](#output-structure)
  - [Token Types](#token-types)
- [Features](#features)
- [Architecture](#architecture)
- [Tested on 500,000+ arXiv Papers](#tested-on-500000-arxiv-papers)
- [Limitations](#limitations)
- [Contributions](#contributions)
- [MIT License](#license)

## Quick Start

### Installation

```bash
pip install git+https://github.com/mrlooi/latex2json.git
```

Requires Python 3.10+.

### Parse a string

```python
from latex2json import TexReader

reader = TexReader()
result = reader.process_text(r"""
\begin{document}
\title{My Paper}
\maketitle
\section{Introduction}
We propose a method for $E = mc^2$.
\subsection{Subsection}
\begin{equation}
E = mc^2
\end{equation}
\end{document}
""")
tokens = result.tokens
```

### Parse files, folders, or archives

```python
from latex2json import TexReader

tex_reader = TexReader()

# .tex file, folder with multiple .tex files, or .tar.gz from arXiv
result = tex_reader.process("/path/to/paper.tar.gz")

# result.tokens contains the parsed token list
json_output = tex_reader.to_json(result)

# Clean up temp files if processing an archive
result.cleanup()
```

`TexReader.process()` accepts `.tex` files, directories, `.gz`, and `.tar.gz` archives. It auto-detects the main `.tex` file, resolves `\input`/`\include` dependencies, and parses bundled `.sty`/`.cls`/`.bib` files.

### Error handling

```python
from latex2json import TexReader, TexProcessingError

try:
    result = TexReader().process("paper.tar.gz")
except FileNotFoundError:
    pass  # File doesn't exist
except TexProcessingError as e:
    pass  # Wraps extraction/processing failures
except RuntimeError as e:
    pass  # Infinite macro recursion detected
```

The parser degrades gracefully: unsupported commands become `command` tokens, missing `.bib`/`.sty` files are skipped with a warning, and infinite recursion is caught by automatic depth limits.


## Output Structure

The parser produces a JSON array of semantic tokens preserving document hierarchy:

```json
[
  {
    "type": "title",
    "content": [{ "type": "text", "content": "My Title" }]
  },
  {
    "type": "document",
    "content": [
      {
        "type": "abstract",
        "content": [{ "type": "text", "content": "This is my abstract" }]
      },
      {
        "type": "section",
        "title": [{ "type": "text", "content": "Introduction" }],
        "level": 1,
        "numbering": "1",
        "content": [
          { "type": "text", "content": "Some text here", "styles": ["bold"] },
          {
            "type": "equation",
            "content": "E = mc^2",
            "display": "block",
            "numbering": "1"
          }
        ]
      }
    ]
  }
]
```

For more examples, see [tests/renderer/test_json_renderer.py](tests/renderer/test_json_renderer.py).

### Token Types

#### Document Structure

- `document` - Root document container
- `title` - Document title
- `section` - Section headers (includes subsections via `level`)
- `paragraph` - Text paragraphs
- `abstract` - Document abstract
- `appendix` - Appendix sections

#### Content Elements

- `text` - Plain text with optional `styles` array
- `quote` - Quoted text content
- `equation` - Math equations (`display`: `"inline"` or `"block"`)
- `equation_array` - Align/matrix/array environments
- `figure`, `subfigure` - Figure environments
- `table`, `subtable` - Table environments
- `tabular` - Table content structure
- `caption` - Captions for figures and tables
- `list` - Enumerated or itemized lists
- `item` - List items
- `code` - Code blocks
- `algorithm`, `algorithmic` - Algorithm environments

#### Graphics

- `includegraphics` - Image references
- `includepdf` - PDF references
- `diagram` - tikz/pgfpicture/picture as verbatim LaTeX

#### References

- `citation` - Bibliography citations
- `ref` - Cross-references
- `url` - URL links
- `footnote` - Footnotes
- `bibliography` - Bibliography section
- `bibitem` - Bibliography entries

#### Metadata

- `author` - Author information
- `email` - Email addresses
- `affiliation` - Author affiliations
- `keywords` - Document keywords
- `address` - Address information

#### Fallback

- `command` - Unsupported LaTeX commands (preserved rather than dropped)
- `environment` - Generic environments
- `math_env` - Generic math environments
- `group` - Grouped content

## Features

### Macro expansion

- Resolves `\newcommand`, `\def`, `\let`, `\renewcommand`, `\csname` and other command definitions
- Recursive expansion across nested content
- Proper scoping — `\begin{env}` pushes scope, `\end{env}` pops it
- Complex parameter substitution (e.g. `##1` in nested definitions)
- Starred and non-starred command variants
- Command defaults and optional arguments

### Environment handling

- Nested environments (e.g. tabular within tabular)
- Math environments: inline, block, align, gather, array, matrix
- Tables: multi-row/multi-column, mixed content
- Lists, figures, algorithms, theorems
- Drawing environments (tikz, pgfpicture) preserved as verbatim `diagram` tokens

### Style file processing

- Parses real-world `.sty` and `.cls` files bundled with papers
- Handles custom class files, package options, conditional definitions
- Unsupported commands skipped gracefully

### expl3 support

Partial support for LaTeX3 programming layer — handles common expl3 modules used in modern packages:

`bool`, `clist`, `cs`, `dim`, `exp`, `file`, `fp`, `group`, `int`, `io`, `keys`, `msg`, `peek`, `prg`, `prop`, `quark`, `regex`, `seq`, `skip`, `str`, `tl`, `token`

Not all expl3 primitives are covered, but enough to parse most papers that use expl3-based packages.

### Numbering

LaTeX2JSON implements LaTeX's full counter system to produce accurate numbering for sections, equations, figures, tables, theorems, and captions — as close to real LaTeX-to-PDF output as possible.

- **Hierarchical numbering** — Sections produce `1`, `1.1`, `1.2.3`, etc. Stepping a parent counter resets its children, matching LaTeX behavior.
- **Equation numbering** — Block equations are numbered sequentially. `\nonumber`/`\notag` suppress numbering. `\tag{...}` overrides it. In `align` environments, each row is numbered independently.
- **Sub-numbering** — `subequation` produces `1a`, `1b`; `subfigure`/`subtable` produce `1a`, `1b` under their parent float.
- **`\numberwithin` / `\counterwithin`** — `\numberwithin{equation}{section}` makes equations number as `1.1`, `1.2` within each section, resetting on section change.
- **Counter commands** — `\setcounter`, `\addtocounter`, `\stepcounter`, `\refstepcounter`, `\newcounter`, `\value` all work.
- **Format styles** — Arabic (`1, 2, 3`), roman (`i, ii, iii`), Roman (`I, II, III`), alpha (`a, b, c`), Alpha (`A, B, C`). Appendix sections default to alphabetic (`A`, `B`, `C`).
- **`\the<counter>` overrides** — Custom numbering formats via `\renewcommand{\theequation}{...}` are respected.
- **Theorem numbering** — `\newtheorem` environments get their own counters with optional parent counters, producing `Theorem 1`, `Lemma 1.1`, etc.

Every numberable node in the output JSON includes a `numbering` field:

```json
{ "type": "section", "level": 2, "numbering": "3.1", "title": [...] }
{ "type": "equation", "display": "block", "numbering": "3.2", "content": "..." }
{ "type": "caption", "numbering": "1a", "content": [...] }
```

### Bibliography

- Parses `.bib` and `.bbl` files
- Resolves `\cite`, `\citep`, `\citet` and variants
- Handles multiple citations and citation notes

## Architecture

```
Raw LaTeX → Tokenizer → Expander → Parser → Renderer → JSON AST
```

1. **Tokenization** (`latex2json/tokens/`) — Converts raw LaTeX text into tokens with proper catcode handling
2. **Expansion** (`latex2json/expander/`) — Resolves macro definitions, expansions, and LaTeX primitives
3. **Parsing** (`latex2json/parser/`) — Converts expanded tokens into semantic AST nodes
4. **Rendering** (`latex2json/renderer/`) — Transforms AST into final JSON output

### Key Components

| Component | Location | Description |
|-----------|----------|-------------|
| **TexReader** | `tex_reader.py` | Main entry point. Handles files, folders, and archives. |
| **ExpanderCore** | `expander/expander_core.py` | Core macro expansion engine with state and scope management. |
| **MacroRegistry** | `expander/macro_registry.py` | Stores macro definitions and maps commands to handlers. |
| **ParserCore** | `parser/parser_core.py` | Converts expanded tokens to semantic AST nodes. |
| **Handlers** | `expander/handlers/`, `parser/handlers/` | Specialized processors for primitives, environments, conditionals, bibliography, etc. |
| **Nodes** | `nodes/` | AST node types — `TextNode`, `CommandNode`, sections, equations, tables, captions. |

### Extending the Parser

To add support for a new LaTeX command or package:

- **Expander-level** (macro expansion): Add a handler in `expander/handlers/`. This is where you teach the system how to expand a new command into tokens.
- **Parser-level** (semantic output): Add a handler in `parser/handlers/`. This is where you define what AST node a command produces.
- **Package-level**: Package handlers live in `expander/packages/` and register commands that a specific LaTeX package provides.

~1000 unit tests mirror the main package structure (`tests/expander/`, `tests/parser/`, `tests/nodes/`, `tests/tokens/`).

## Tested on 500,000+ arXiv Papers

LaTeX2JSON has parsed **500k+ papers** across math, physics, computer science, and 40+ other arXiv categories — from recent 2025 submissions to highly-cited classics. It powers [ScienceStack](https://sciencestack.ai), which serves these as structured APIs for AI agents, RAG pipelines, and research tools.

Papers span a good range of LaTeX complexity:

- [2303.08774] GPT-4 Technical Report
- [1706.03762] Attention Is All You Need
- [2307.09288] Llama 2
- [2501.12948] DeepSeek-R1
- [2304.02643] Segment Anything
- [1703.06870] Mask R-CNN
- [1509.05363] The Erdos Discrepancy Problem
- [math/0503066] Stable Signal Recovery from Incomplete and Inaccurate Measurements
- [hep-th/0603057] Dynamics of Dark Energy

View any parsed paper live at [`sciencestack.ai/paper/{arxiv_id}`](https://sciencestack.ai).

## Limitations

- **Macro expansion is best-effort.** The expander handles standard LaTeX primitives and common packages, but some `.sty` files use low-level TeX internals that aren't fully supported. Unexpanded macros are emitted as `command` tokens rather than crashing.
- **LaTeX is Turing-complete.** Some macro patterns can trigger infinite recursion. The expander has automatic recursion detection and depth limits to catch these, but pathological cases exist.
- Drawing commands (tikz, pgfpicture, Chess, etc.) are preserved as verbatim blocks, not parsed
- Does not preserve visual formatting (page layout, column arrangement, table styling)
- Font and symbol declarations (`\newfont`, `\newsymbol`) not fully supported

### Numbering Limitations

Due to the single-pass architecture:

1. **Restatable Environments** — `\MainResult*` shows the counter state at time of call, not final numbering after all restatements
2. **ContinuedFloat** — Not handled; continued floats receive new numbering
3. **`showonlyrefs`** — All equations are numbered regardless of whether they're referenced

## Contributions

Areas where help is needed:

1. **Broader expl3 coverage** — many modules are supported but not all primitives
2. **Complex `@if` conditionals and LaTeX internals**
3. **Additional package commands** — if you find an unsupported command, add a handler

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/some-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/some-feature`)
5. Open a Pull Request

Please ensure your PR includes a clear description and updated tests where applicable.

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.
