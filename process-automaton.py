#!/usr/bin/env python

import re
import sys
from sage.all import *


def read_up_to(inp, expr):
    for line in inp:
        m = re.fullmatch(expr, line.strip())
        if m: return m

    raise Exception("Failed to match expr")


def parse_automaton(inp):
    read_up_to(inp, "Initial state: 0")
    final = list(map(int, read_up_to(inp, "Accepting states: ([0-9 ]+)")[1].split()))
    states = int(read_up_to(inp, "Automaton has ([0-9]+) states and [0-9]+ BDD-nodes")[1])

    initial = [ 0 ]*states
    initial[1] = 1
    final = [ 1 if i in final else 0 for i in range(states) ]

    assert next(inp).strip() == "Transitions:"
    step = [ [ 0 ]*states for _ in range(states) ]
    for line in inp:
        line = line.strip()
        if line == "": break
        m = re.fullmatch("State ([0-9]+): ([01X]+) -> state ([0-9]+)", line)
        assert m, f"Failed to match line '{line}'"

        from_ = int(m[1])
        to = int(m[3])
        edges = 2 ** m[2].count('X')

        step[from_][to] += edges

    return initial, step, final


def automaton_to_generating_function(initial, step, final):
    n = len(initial)
    x = SR.var("x", QQ)

    initial = matrix(QQ, [ initial ])
    final = matrix(QQ, [ final ]).transpose()
    step = matrix(QQ, step)
    M = matrix.identity(n) - x * step

    num = (initial * M.adjugate() * final)[0, 0].rational_expand()
    den = M.det().rational_expand()
    return (num / den).simplify_full()
    

I, S, F = parse_automaton(sys.stdin)

if len(sys.argv) >= 2 and sys.argv[1]:
    with open(sys.argv[1], "w") as f:
        print(f"states = {len(I)}", file=f)
        print(f"initial = {I}", file=f)
        print(f"final = {F}", file=f)
        print("step = [", file=f)
        for r in S: print(f"  {r},", file=f)
        print("]", file=f)

print(automaton_to_generating_function(I, S, F))


