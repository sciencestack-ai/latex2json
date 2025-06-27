import logging
from typing import Dict, List, Optional
from latex2json.nodes import ASTNode, CommandNode, TextNode, TabularNode
from latex2json.parser.parser import Parser


class JSONRenderer:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.parser = Parser(logger=logger)
        self.logger = logger

    def parse(self, text: str) -> Dict[str, List[Dict]]:
        nodes = self.parser.parse(text, postprocess=True)
        return self.convert_to_json(nodes)

    def convert_to_json(self, nodes: List[ASTNode]) -> List[Dict]:
        output = []

        for node in nodes:
            out_dict = node.to_json()
            if not out_dict:
                continue
            output.append(out_dict)

        return output


if __name__ == "__main__":
    renderer = JSONRenderer()
    text = r"""
    \def\aaa{AAA}
    \subsection{INTRODUCTION} \label{sec:introduction}
\begin{tabular}{cc}
    \multicolumn{2}{c}{1} & \textbf{2} & 
        \begin{itemize}
            \item item1 \aaa

        \end{itemize} 
    
       & 5 \\ 
    3 & 4 
\end{tabular}

\appendix 
\section{APPENDIX A}
\paragraph{PARA A}
    """
    json = renderer.parse(text)
    print(json)
