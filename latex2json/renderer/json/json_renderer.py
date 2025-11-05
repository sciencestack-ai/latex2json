import logging
from typing import Dict, List, Optional
from latex2json.expander.expander import Expander
from latex2json.nodes import ASTNode
from latex2json.nodes.node_types import NodeTypes
from latex2json.parser import ParserCore, ParserParallel

INLINE_TYPES = [
    NodeTypes.TEXT,
    NodeTypes.REF,
    NodeTypes.CITATION,
    NodeTypes.URL,
    NodeTypes.FOOTNOTE,
    NodeTypes.COMMAND,
]

ACCEPTED_COMMAND_NAMES = ["and"]  # \and for delimiting author blocks


def is_token_inline(token: Dict) -> bool:
    if not isinstance(token, dict):
        return False
    typing = token.get("type")
    if typing in INLINE_TYPES:
        return True
    elif typing == NodeTypes.EQUATION and token.get("display") != "block":
        return True
    return False


def is_math_token(token: Dict) -> bool:
    if not isinstance(token, dict):
        return False
    return token.get("type") in [
        NodeTypes.EQUATION,
        NodeTypes.EQUATION_ARRAY,
    ]


def is_text_token(token: Dict) -> bool:
    if not isinstance(token, dict):
        return False
    return token.get("type") == NodeTypes.TEXT


def is_katex_compatible_token(token: Dict) -> bool:
    if not isinstance(token, dict):
        return False
    return token.get("type") in [
        NodeTypes.TEXT,
        NodeTypes.COMMAND,
        NodeTypes.EQUATION_ARRAY,
        NodeTypes.EQUATION,
        NodeTypes.ROW,
    ]


def strip_whitespace_json_tokens(tokens: List[Dict]):
    if not tokens:
        return tokens

    # lstrip whitespace from start tokens
    while tokens and is_text_token(tokens[0]):
        text: str = tokens[0].get("content")
        if text and text.strip():
            tokens[0]["content"] = text.lstrip()
            break
        tokens.pop(0)

    # rstrip whitespace from end tokens
    while tokens and is_text_token(tokens[-1]):
        text: str = tokens[-1].get("content")
        if text and text.strip():
            tokens[-1]["content"] = text.rstrip()
            break
        tokens.pop(-1)

    # Then remove all empty text tokens in between
    stripped_tokens = []
    N = len(tokens)
    for i, token in enumerate(tokens):
        if not token:
            continue
        if is_text_token(token):
            content: str = token.get("content")
            if not content:
                continue
            # check if text token has content
            if content.strip():
                # also lstrip the content if prev token is not inline.
                if i > 0 and not is_token_inline(tokens[i - 1]):
                    token["content"] = content.lstrip()
                stripped_tokens.append(token)
            else:
                # if content is "\n", preserve it and add to next token if next is also a text token
                if i < N - 1 and is_text_token(tokens[i + 1]):
                    next_token = tokens[i + 1]
                    next_content: str = next_token.get("content")
                    if not next_content:
                        continue
                    new_str = content.replace(" ", "") + next_content.lstrip(" ")
                    next_token["content"] = new_str
        else:
            stripped_tokens.append(token)

    return stripped_tokens


class JSONRenderer:
    parser: ParserCore

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        n_processors: int = 1,
        expander: Optional[Expander] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.n_processors = n_processors

        self._init_parser(expander)

    def _init_parser(self, expander: Optional[Expander]):
        if expander is None:
            expander = Expander(logger=self.logger)

        self.parser = ParserParallel(
            logger=self.logger, n_processors=self.n_processors, expander=expander
        )

    @property
    def expander(self) -> Expander:
        return self.parser.expander

    def clear(self, expander: Optional[Expander] = None):
        self._init_parser(expander)

    def get_colors(self):
        return self.parser.get_colors()

    def parse_file(
        self, file_path: str, organize_hierachy=True
    ) -> Optional[Dict[str, List[Dict]]]:
        nodes = self.parser.parse_file(
            file_path, postprocess=True, resolve_cross_document_references=True
        )
        if not nodes:
            return None
        self.logger.info(f"Parsed {len(nodes)} nodes, converting to json...")
        return self.convert_nodes_to_json(nodes, organize_hierachy=organize_hierachy)

    def parse(self, text: str, organize_hierachy=True) -> Dict[str, List[Dict]]:
        nodes = self.parser.parse(
            text, postprocess=True, resolve_cross_document_references=True
        )
        self.logger.info(f"Parsed {len(nodes)} nodes, converting to json...")
        json_tokens = self.convert_nodes_to_json(
            nodes, organize_hierachy=organize_hierachy
        )

        return json_tokens

    def convert_nodes_to_json(
        self, nodes: List[ASTNode], organize_hierachy=True
    ) -> List[Dict]:
        output = []

        for node in nodes:
            out_dict = node.to_json()
            if not out_dict:
                continue
            output.append(out_dict)

        # strip out all tokens before the first document
        # but also ensure that any bibliography token before first document is not lost
        first_document_idx = -1
        bib_token = None
        for i, token in enumerate(output):
            if isinstance(token, dict):
                token_type = token.get("type")
                if token_type == NodeTypes.DOCUMENT:
                    first_document_idx = i
                    break
                elif token_type == NodeTypes.BIBLIOGRAPHY:
                    bib_token = token
        if first_document_idx != -1:
            output = output[first_document_idx:]
        if bib_token:
            # add back bib token
            output.insert(0, bib_token)

        if organize_hierachy:
            organized = self._recursive_organize(output)
            # Apply recursive whitespace stripping
            output = self._recursive_postprocess(organized)

        return [t for t in output if t]

    def _manage_stack(
        self,
        token: Dict,
        stack: List[Dict],
        organized: List[Dict],
        parent_stack: Optional[List[Dict]] = None,
    ):
        """Helper function to manage stack operations for sections and paragraphs"""
        # Clear lower stacks if needed
        while stack and stack[-1]["level"] >= token["level"]:
            stack.pop()

        # Determine where to add the token
        target = (
            parent_stack[-1]["content"]
            if parent_stack
            else (stack[-1]["content"] if stack else organized)
        )
        target.append(token)

        token["content"] = []
        stack.append(token)

    def _recursive_organize(
        self, tokens: List[Dict], parent_token: Optional[Dict] = None
    ):
        organized = []
        section_stack = []
        paragraph_stack = []
        root = organized  # Default root for content

        def get_current_target():
            if paragraph_stack:
                return paragraph_stack[-1]["content"]
            if section_stack:
                return section_stack[-1]["content"]
            return root

        # first, preprocess tokens to remove all tokens after \end{document}
        is_parent_document = parent_token and parent_token["type"] == NodeTypes.DOCUMENT
        if not is_parent_document:
            last_document_idx = -1
            for i, token in enumerate(tokens):
                if isinstance(token, dict) and token["type"] == NodeTypes.DOCUMENT:
                    last_document_idx = i
                    # don't break here due to possibility of sibling documents i.e. \subfile{...}
                    # break
            if last_document_idx != -1:
                # strip out all tokens after last document env (mimics latex document structure i.e. tokens after \end{document} are not included)
                tokens = tokens[: last_document_idx + 1]

        # then organize them into hierachies with nested 'content'
        for token in tokens:
            if not isinstance(token, dict):
                get_current_target().append(token)
                continue

            # Handle appendix declaration
            if token["type"] == NodeTypes.APPENDIX:
                section_stack.clear()
                paragraph_stack.clear()

                if not token.get("content"):
                    token["content"] = []
                else:
                    token["content"] = self._recursive_organize(
                        token["content"], parent_token=token
                    )

                if organized and organized[-1]["type"] == NodeTypes.APPENDIX:
                    # if previous token is also an appendix, merge content
                    organized[-1]["content"] += token["content"]
                    continue
                root = token["content"]  # Switch root to appendix content
                organized.append(token)  # add appendix token itself to organized
                continue

            # Handle other nested content
            if isinstance(token.get("content"), list):
                token["content"] = self._recursive_organize(
                    token["content"],
                    parent_token=token,
                )

            # Handle special token types
            if token["type"] == NodeTypes.BIBLIOGRAPHY:
                section_stack.clear()
                paragraph_stack.clear()
                organized.append(token)
            elif token["type"] == NodeTypes.SECTION:
                paragraph_stack.clear()

                self._manage_stack(token, section_stack, root)
            elif token["type"] == NodeTypes.PARAGRAPH:
                self._manage_stack(token, paragraph_stack, root, section_stack)
            else:
                get_current_target().append(token)

        return organized

    def _reorder_dict_keys(self, d: Dict) -> Dict:
        """Helper function to reorder dictionary to ensure 'type' is first key and 'content' is the last key"""
        if not isinstance(d, dict):
            return d

        # If there's no type key, return as is
        if "type" not in d:
            return d

        # Get type and content values and remove from dict
        type_val = d.pop("type")
        content = d.pop("content", None)

        # Create new dict starting with type
        result = {"type": type_val}

        # Add remaining items in sorted order
        for k in sorted(d.keys()):
            result[k] = d[k]

        # Add content back as last item if it existed
        if content is not None:
            result["content"] = content

        return result

    def _sanitize_equation_token(self, token: Dict) -> Dict:
        if not isinstance(token, dict):
            return token
        if token.get("type") != NodeTypes.EQUATION:
            return token
        # strip off display attribute if inline
        if token.get("display") == "inline":
            del token["display"]
        content = token.get("content")
        if content and isinstance(content, list):
            # check if all content is "text"
            if all(is_text_token(item) for item in content):
                # if so, merge into a single string
                token["content"] = "".join(item.get("content", "") for item in content)
            else:
                # check if single non-text or command token, return that directly instead
                # e.g. single reference token inside equation e.g. $\ref{eq:1}$ -> \ref{eq:1}
                if len(content) == 1:
                    item = content[0]
                    if not is_katex_compatible_token(item):
                        return item
        return token

    def _recursive_postprocess(
        self, tokens: List[Dict], strip_whitespace_tokens=True
    ) -> List[Dict]:
        """Recursively strip whitespace from tokens and their nested content."""
        if not isinstance(tokens, list):
            return tokens

        # strip whitespace from tokens
        if strip_whitespace_tokens:
            tokens = strip_whitespace_json_tokens(tokens)

        for i, token in enumerate(tokens):
            if not isinstance(token, dict):
                if isinstance(token, list):
                    tokens[i] = self._recursive_postprocess(
                        token, strip_whitespace_tokens=strip_whitespace_tokens
                    )
                continue

            token_type = token.get("type", "")

            if token_type == NodeTypes.EQUATION:
                tokens[i] = self._sanitize_equation_token(token)
                continue
            elif "content" in token and isinstance(token["content"], list):
                # don't strip whitespace from math tokens e.g. preserve empty align cells
                token["content"] = self._recursive_postprocess(
                    token["content"],
                    strip_whitespace_tokens=strip_whitespace_tokens
                    and not is_math_token(token),
                )

            if token_type == NodeTypes.ENVIRONMENT:
                token_name = token.get("name", "")
                if token_name == "quote":
                    # make quote type
                    token["type"] = NodeTypes.QUOTE

            # Reorder the dictionary to ensure 'content' field is last.
            # This makes it easier to read the json metadata format before 'content'
            tokens[i] = self._reorder_dict_keys(token)

        for token in tokens:
            if isinstance(token, dict) and token.get("type") == NodeTypes.COMMAND:
                command_name: str = token.get("command", "")
                if command_name.lower() not in ACCEPTED_COMMAND_NAMES:
                    self.logger.warning(f"Found unknown command: {command_name}")

        return tokens


if __name__ == "__main__":
    from latex2json.utils.logger import setup_logger

    logger = setup_logger(level=logging.INFO)
    renderer = JSONRenderer(logger=logger)
    text = r"""
    \title{My Title}

    \author{
        Mr X \somecmd \\
        University of XYZ \\
    }

    \begin{document}

    \begin{abstract}
    This is my abstract, \texttiny{cool yes?}
    \end{abstract}

    \paragraph{This is my paragraph}
    YEAAA baby

    \section{Intro $1+1$} \label{sec:intro}

        Some text here, $1+1=2$:
        \begin{equation}
            E = mc^2 \\ x = 1
        \end{equation}

        \begin{figure}[h]
            \includegraphics[page=1]{mypdf.pdf}
            \caption{My figure, from \cite[\textsc{p. 42}]{bibkey1}}
            \begin{subfigure}[b]{0.45\textwidth}
                \caption{Subfigure caption}
            \end{subfigure}
        \end{figure}

        \subsection{SubIntro}
        My name is \textbf{John Doe} \textbf{Sss} ahama \verb|my code|

        \begin{theorem}[$T=1$]
            Theorem 1
        \end{theorem}
        
        % \begin{proof}
        %    \bf Proof of theorem 1
        % \end{proof}

        \subsection*{SubIntro2}
        SUBINTRO 2
        \paragraph{Paragraph me}
        Hi there this is paragraph

        \begin{theorem*}
            Theorem 2
        \end{theorem*}

        \hyperref[sec:intro]{\textbf{Back to intro}}
        \subsection{Last sub section}
            \subsubsection{S3}
            \subsubsection{S4}

    \section{Conclusion}
        TLDR: Best paper

        \subsection{mini conclusion}
        Mini conclude
        
        \begin{align*}
            F = ma
        \end{align*}

        \begin{proposition}
            Proposition X
        \end{proposition}

        \begin{algorithm}
            \caption{Binary Search}
        \end{algorithm}        

        \begin{tabular}{|c|c|}
            \hline
            Cell 1 & \textbf{Cell 2} & 3 \\
            \hline
            \multicolumn{2}{|c|}{Spanning Cell} &  \\
            & H1 \& H2 & 
            \hline
        \end{tabular}

        \begin{description}
        \item[\textbf{Hello}] World
        \item[Hello] % nested env
            \paragraph{This nested env inside}
                \begin{enumerate}
                \item 1
                \item 2
                \end{enumerate}
            World
        \end{description}

        \begin{tikzpicture}
            \draw (0,0) -- (1,1);
        \end{tikzpicture}

    \appendix

    \section{My Appendix Section}
        Here goes my appendix...
    
        \subsection{Sub appendix 1}
        Yea this appendix is nice

        \subsection{Sub appendix 2}

    \begin{thebibliography}{99}
    \bibitem[Title]{bibkey1} Some content \tt cool
    \end{thebibliography}

    \end{document}
    """.strip()

    text = r"""
    \newtheorem{theorem}{Theorem}

    \newcommand{\pow}[2][2]{#2^{#1}}
    \newcommand{\dmodel}{d_{\text{model}}}

    \newcommand{\tensor}[3]{\mathbf{#1}_{#2}^{#3}}
    
    % Command with 1 optional and 2 required arguments
    \newcommand{\norm}[3][2]{\|#2\|_{#3}^{#1}}
    
    \newcommand{\integral}[4][0]{\int_{#1}^{#2} #3 d#4}
    
    % Command using other defined commands
    \newcommand{\tensorNorm}[4]{\norm{\tensor{#1}{#2}{#3}}{#4}}

    \begin{theorem} \label{thm:1}
    
    $\tensor{T}{i}{j}$ and $\norm[p]{x}{2}$ and $\norm{y}{1}$
    $\integral{b}{f(x)}{x}$ and $\integral[a]{b}{g(x)}{x}$
    $\tensorNorm{T}{i}{j}{\infty}$

    \end{theorem}

    \begin{equation} \label{eq:1}
    \int_{3} \& \{
    \end{equation}

    \begin{align}
equation1 &= expression1 \label{eq:first} \\
equation2 &= expression2 \nonumber \label{eq:second} \\
equation3 &= expression3 \label{eq:third}
\end{align}

\def\xxx{x+1}

\begin{equation} \label{eq:arr}
\begin{array}{c}
long expression &= first part \ref{eq:1} \\
                &\quad + second part \xxx \\
                &\quad + third part 
\end{array}
\end{equation}

\begin{comment}
Some comment
\end{comment}

\begin{appendices}
\section{Appendix 1}
Appendix 1 content

\section{Appendix 2}
Appendix 2 content
\end{appendices}
"""

    text = r"""
\begin{align}
P &= 33 \\ 
  &= 44
\end{align}
""".strip()

    json = renderer.parse(text)
    parser = renderer.parser
    print(json)

    # json = renderer.parse_file(
    #     "/Users/cj/Documents/python/latex2json/tests/samples/main.tex"
    # )
