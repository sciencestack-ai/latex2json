from latex2json.parser import Parser, ParserParallel

import os


def test_parser_n_parallel_are_same():
    parser = Parser()
    parser_parallel = ParserParallel(n_processors=3)

    dir_path = os.path.dirname(os.path.abspath(__file__))
    sample_dir_path = os.path.join(dir_path, "../samples")
    file_path = os.path.join(sample_dir_path, "main.tex")
    out = parser.parse_file(file_path)
    out_parallel = parser_parallel.parse_file(file_path)

    assert len(out) >= 1
    assert len(out) == len(out_parallel)
    out_str = parser.convert_nodes_to_str(out)
    out_parallel_str = parser_parallel.convert_nodes_to_str(out_parallel)

    assert out_str.replace("\n", "") == out_parallel_str.replace("\n", "")
