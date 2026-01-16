r"""
expl3 (LaTeX3) syntax handlers.

This module provides handlers for the expl3 programming layer, which uses
a different syntax with _ and : as part of command names.

=============================================================================
IMPLEMENTATION STRATEGY
=============================================================================

When adding new expl3 handlers, follow these principles:

1. **Transform to LaTeX equivalents when possible** (let existing handlers work):
   - \tl_new:N \l_my_tl      -> push \def\l_my_tl{}
   - \tl_set:Nn \l_my_tl {x} -> push \def\l_my_tl{x}
   - \tl_gset:Nn             -> push \global\def
   - \cs_new_eq:NN           -> push \let
   - \cs_new:Npn             -> push \def

2. **Evaluate in Python when no clean LaTeX equivalent exists**:
   - \str_if_eq:nnTF  -> compare strings in Python, push winning branch
   - \tl_if_empty:nTF -> check empty in Python, push winning branch
   - \int_compare:nTF -> evaluate comparison in Python, push winning branch
   - \int_eval:n      -> evaluate arithmetic in Python, return result tokens

3. **Why this approach**:
   - Pushing LaTeX equivalents reuses existing well-tested handlers
   - Avoids duplicating complex logic (scoping, expansion, etc.)
   - Python evaluation is simpler than reconstructing \ifnum...\else...\fi
   - Conditionals just need to pick the right branch - no need for full TeX if/fi

4. **Pattern for conditionals (TF/T/F variants)**:
   - TF: parse test + true_branch + false_branch, push winner
   - T:  parse test + true_branch, push if true (else nothing)
   - F:  parse test + false_branch, push if false (else nothing)

=============================================================================
MODULE ORGANIZATION
=============================================================================

The expl3 handlers are organized by l3 module:
- syntax.py  - ExplSyntaxOn/Off, ProvidesExpl*
- cs.py      - Control sequence functions (cs_new_eq, cs_if_exist, etc.)
- tl.py      - Token list functions (tl_new, tl_set, tl_if_empty, etc.)
- int.py     - Integer functions (int_new, int_set, int_compare, etc.)
- exp.py     - Expansion control (exp_args, exp_not, etc.)
- str.py     - String functions (str_if_eq, str_case, etc.)
- bool.py    - Boolean functions (bool_new, bool_if, etc.)
- seq.py     - Sequence functions (seq_new, seq_clear, etc.)
- clist.py   - Comma list functions (clist_new, clist_clear, etc.)
- prg.py     - Programming utilities (prg_do_nothing, prg_return_*, etc.)
- quark.py   - Quark special values (q_no_value, quark_if_no_value, etc.)
- group.py   - Grouping (group_begin, group_end)
- use.py     - Use functions (use:n, use_none:n, etc.)
=============================================================================
"""

from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.expl3.syntax import register_syntax_handlers
from latex2json.expander.handlers.expl3.cs import register_cs_handlers
from latex2json.expander.handlers.expl3.tl import register_tl_handlers
from latex2json.expander.handlers.expl3.int import register_int_handlers
from latex2json.expander.handlers.expl3.fp import register_fp_handlers
from latex2json.expander.handlers.expl3.exp import register_exp_handlers
from latex2json.expander.handlers.expl3.str import register_str_handlers
from latex2json.expander.handlers.expl3.bool import register_bool_handlers
from latex2json.expander.handlers.expl3.seq import register_seq_handlers
from latex2json.expander.handlers.expl3.clist import register_clist_handlers
from latex2json.expander.handlers.expl3.prop import register_prop_handlers
from latex2json.expander.handlers.expl3.prg import register_prg_handlers
from latex2json.expander.handlers.expl3.quark import register_quark_handlers
from latex2json.expander.handlers.expl3.group import register_group_handlers
from latex2json.expander.handlers.expl3.use import register_use_handlers
from latex2json.expander.handlers.expl3.msg import register_msg_handlers
from latex2json.expander.handlers.expl3.regex import register_regex_handlers
from latex2json.expander.handlers.expl3.dim import register_dim_handlers


def register_expl3_handlers(expander: ExpanderCore) -> None:
    """Register all expl3 handlers."""
    register_syntax_handlers(expander)
    register_cs_handlers(expander)
    register_tl_handlers(expander)
    register_int_handlers(expander)
    register_fp_handlers(expander)
    register_dim_handlers(expander)
    register_exp_handlers(expander)
    register_str_handlers(expander)
    register_bool_handlers(expander)
    register_seq_handlers(expander)
    register_clist_handlers(expander)
    register_prop_handlers(expander)
    register_prg_handlers(expander)
    register_quark_handlers(expander)
    register_group_handlers(expander)
    register_use_handlers(expander)
    register_msg_handlers(expander)
    register_regex_handlers(expander)
