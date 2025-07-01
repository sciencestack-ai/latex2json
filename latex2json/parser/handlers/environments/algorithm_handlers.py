from latex2json.nodes import AlgorithmicNode, AlgorithmNode
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import Token, TokenType


def algorithm_env_handler(parser: ParserCore, token: Token):
    env = parser.parse_environment(token)
    algorithm_node = AlgorithmNode(env.body, env.numbering)
    algorithm_node.labels = env.labels
    return [algorithm_node]


def algorithmic_env_handler(parser: ParserCore, token: Token):
    # parse algorithmic environment verbatim
    tokens = parser.parse_tokens_until(
        lambda tok: tok == Token(TokenType.ENVIRONMENT_END, "algorithmic"),
        consume_predicate=True,
    )
    return [AlgorithmicNode(parser.convert_tokens_to_str(tokens).strip())]


def register_algorithm_handlers(parser: ParserCore):
    parser.register_env_handler("algorithm", algorithm_env_handler)
    parser.register_env_handler("algorithmic", algorithmic_env_handler)


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()

    register_algorithm_handlers(parser)

    text = r"""
\begin{algorithm}
\caption{An algorithm with caption}\label{alg:cap}
\begin{algorithmic}
\Require $n \geq 0$
\Ensure $y = x^n$
\State $y \gets 1$
\State $X \gets x$
\State $N \gets n$
\While{$N \neq 0$}
\If{$N$ is even}
    \State $X \gets X \times X$
    \State $N \gets \frac{N}{2}$  \Comment{This is a comment}
\ElsIf{$N$ is odd}
    \State $y \gets y \times X$
    \State $N \gets N - 1$
\EndIf
\EndWhile
\end{algorithmic}
\end{algorithm}

"""
    out = parser.parse(text, postprocess=True)
