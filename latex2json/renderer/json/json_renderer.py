import logging
from typing import Dict, List, Optional
from latex2json.nodes import ASTNode
from latex2json.parser.parser import Parser


def strip_whitespace_json_tokens(tokens: List[Dict]):
    if not tokens:
        return tokens

    # First strip whitespace from start/end tokens
    while tokens and isinstance(tokens[0], dict) and tokens[0].get("type") == "text":
        text: str = tokens[0].get("content")
        if text and text.strip():
            tokens[0]["content"] = text.lstrip()
            break
        tokens.pop(0)

    while tokens and isinstance(tokens[-1], dict) and tokens[-1].get("type") == "text":
        text: str = tokens[-1].get("content")
        if text and text.strip():
            tokens[-1]["content"] = text.rstrip()
            break
        tokens.pop(-1)

    # Then remove all empty text tokens in between
    stripped_tokens = []
    for token in tokens:
        if isinstance(token, dict) and token.get("type") == "text":
            if token.get("content").strip():
                stripped_tokens.append(token)
        else:
            stripped_tokens.append(token)

    return stripped_tokens


class JSONRenderer:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.parser = Parser(logger=self.logger)

    def get_colors(self):
        return self.parser.get_colors()

    def parse_file(
        self, file_path: str, organize_hierachy=True
    ) -> Optional[Dict[str, List[Dict]]]:
        nodes = self.parser.parse_file(file_path, postprocess=True)
        if not nodes:
            return None
        self.logger.info(f"Parsed {len(nodes)} nodes, converting to json...")
        return self.convert_nodes_to_json(nodes, organize_hierachy=organize_hierachy)

    def parse(self, text: str, organize_hierachy=True) -> Dict[str, List[Dict]]:
        nodes = self.parser.parse(text, postprocess=True)
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

        if organize_hierachy:
            organized = self._recursive_organize(output)
            # Apply recursive whitespace stripping
            organized = self._recursive_postprocess(organized)
            return organized

        return output

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

    def _recursive_organize(self, tokens: List[Dict]):
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

        for token in tokens:
            if not isinstance(token, dict):
                get_current_target().append(token)
                continue

            # Handle appendix declaration
            if token["type"] == "appendix":
                section_stack.clear()
                paragraph_stack.clear()

                if not token.get("content"):
                    token["content"] = []
                else:
                    token["content"] = self._recursive_organize(token["content"])

                if organized and organized[-1]["type"] == "appendix":
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
                )

            # Handle special token types
            if token["type"] == "bibliography":
                section_stack.clear()
                paragraph_stack.clear()
                organized.append(token)
            elif token["type"] == "section":
                paragraph_stack.clear()

                self._manage_stack(token, section_stack, root)
            elif token["type"] == "paragraph":
                self._manage_stack(token, paragraph_stack, root, section_stack)
            else:
                get_current_target().append(token)

        return organized

    def _recursive_postprocess(self, tokens: List[Dict]) -> List[Dict]:
        """Recursively strip whitespace from tokens and their nested content."""
        if not isinstance(tokens, list):
            return tokens

        # strip whitespace from tokens
        tokens = strip_whitespace_json_tokens(tokens)

        for i, token in enumerate(tokens):
            if not isinstance(token, dict):
                if isinstance(token, list):
                    tokens[i] = self._recursive_postprocess(token)
                continue

            if token.get("type") == "equation":
                # strip off display attribute if inline
                if token.get("display") == "inline":
                    del token["display"]
                content = token.get("content")
                if content and isinstance(content, list):
                    # check if all content is "text"
                    if all(
                        isinstance(item, dict) and item.get("type") == "text"
                        for item in content
                    ):
                        # if so, merge into a single string
                        token["content"] = "".join(
                            item.get("content", "") for item in content
                        )
                        continue
            elif "content" in token and isinstance(token["content"], list):
                token["content"] = self._recursive_postprocess(token["content"])

            if token.get("type") == "command":
                self.logger.info(f"Found unknown command: {token.get('command')}")
            elif token.get("type") == "environment":
                if token.get("name") == "quote":
                    # make quote type
                    token["type"] = "quote"

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
    \begin{tabular}{|c|c|}
        \hline
        Cell 1 & \textbf{Cell 2} & 3 \\
        \hline
        \multicolumn{2}{|c|}{Spanning Cell} & \somecmd \\
        & H1 & \textbf{H2} & 
        \hline
    \end{tabular}
"""

    json = renderer.parse(text)

    # json = renderer.parse_file(
    #     "/Users/cj/Documents/python/latex2json/tests/samples/main.tex"
    # )
