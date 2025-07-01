import logging
from typing import Dict, List, Optional
from latex2json.nodes import ASTNode, CommandNode, TextNode, TabularNode
from latex2json.parser.parser import Parser


class JSONRenderer:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.parser = Parser(logger=logger)
        self.logger = logger

    def parse(self, text: str, organize_hierachy=True) -> Dict[str, List[Dict]]:
        nodes = self.parser.parse(text, postprocess=True)
        json_tokens = self.convert_to_json(nodes)
        if organize_hierachy:
            return self._recursive_organize(json_tokens)
        return json_tokens

    def convert_to_json(self, nodes: List[ASTNode]) -> List[Dict]:
        output = []

        for node in nodes:
            out_dict = node.to_json()
            if not out_dict:
                continue
            output.append(out_dict)

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
                root = token["content"]  # Switch root to appendix content
                organized.append(token)
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


if __name__ == "__main__":
    renderer = JSONRenderer()
    text = r"""
    \def\aaa{AAA}
    \section{FIRST}
    \subsection{INTRODUCTION} \label{sec:introduction}
\begin{tabular}{cc}
    \multicolumn{2}{c}{1} & \textbf{2} & 
        \begin{itemize}
            \item item1 \aaa

        \end{itemize} 
    
       & 5 \\ 
    3 & 4 & 
\end{tabular}

\begin{thebibliography}{9}
\bibitem{1}
\end{thebibliography}

\begin{appendices} 
\section{APPENDIX A}
\paragraph{PARA A}
Paragraph SSS
\end{appendices}
    """.strip()
    json = renderer.parse(text)
    print(json)
