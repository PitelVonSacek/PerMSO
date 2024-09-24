#!/usr/bin/python

from ast import literal_eval
from common import get_class, run_mona, read_up_to
from generate_basis import number_to_perm
from perms import gen_mona
from sys import argv
import yaml


def contains_permutation(cls, perm):
    m = gen_mona(cls, check_is_contained=perm)
    automaton = run_mona(m, need_automaton=False)

    if "ANALYSIS\nFormula is unsatisfiable\n" in automaton:
        return False

    b = automaton.index("A satisfying example of least length ")
    be = automaton.index("\n", b) + 1
    m = automaton.index("\n\n", b) + 2
    e = automaton.index("\n\nTotal time:")
    assert m < e
    return automaton[b:be] + automaton[m:e]


if __name__ == "__main__":
    p = literal_eval(argv[1])
    if isinstance(p, int): p = number_to_perm(p)

    if len(argv) >= 3:
        cls = get_class(argv[2], argv[3])
    else:
        cls = yaml.load(sys.stdin, Loader=yaml.SafeLoader)
     
    print(contains_permutation(cls, p))

