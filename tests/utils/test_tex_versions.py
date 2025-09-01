from latex2json.utils.tex_versions import is_content_amstex, is_content_expl3


def test_is_content_amstex():
    text1 = r"""\input amstex
        \documentstyle{amsart}
        \begin{document}"""

    assert is_content_amstex(text1)

    text2 = r"""
\heading 
\endheading
                             
\topmatter
"""
    assert is_content_amstex(text2)

    assert not is_content_amstex(r"\begin{document}")


def test_is_content_expl3():
    text1 = r"""\ProvidesExplPackage{expl3}{2023/01/01}{1.0}{Expl3 package}
        \begin{document}"""
    assert is_content_expl3(text1)

    text2 = r"""
\ExplSyntaxOn
"""
    assert is_content_expl3(text2)


#     text3 = r"""
# \cs_generate_variant:Nn \__nicematrix_color:n { V }
# \cs_set_eq:NN \__nicematrix_old_pgfpointanchor \pgfpointanchor
# \bool_new:N \l__nicematrix_siunitx_loaded_bool
# \hook_gput_code:nnn { begindocument } { . }
# """
#     assert is_content_expl3(text3)

#     assert not is_content_expl3(r"\begin{document}")
