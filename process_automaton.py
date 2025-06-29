#!/usr/bin/env python

from common import read_up_to
import re
import sys
from sage.all import *


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
    """Calculate generating function by solving system of linear equations.

    The generating function is rational with exponents up to n.
    First n + 1 variables are coeffitients of numerator, the next n + 1
    of denominator. Both are ordered from x^0 to x^n.
    """
    n = len(initial)
    initial = matrix(QQ, [ initial ])
    final = matrix(QQ, [ final ]).transpose()
    step = matrix(QQ, step)

    tmp = initial
    values = []
    for _ in range(2*n + 2):
      values.append((tmp*final)[0, 0])
      tmp *= step

    num = matrix(QQ, n + 1, 2*n + 2, lambda r, c: r == c)
    den = matrix(QQ, n + 1, 2*n + 2, lambda r, c: r + n + 1 == c)

    A = matrix(QQ, 2*n + 2, 2*n + 2)
    b = vector(QQ, 2*n + 2)
    for i in range(2*n + 1):
      A[i,:] = num[0,:]
      b[i] = values[i]

      num -= values[i] * den
      num[:-1,:] = num[1:,:]
      num[-1,:] = 0

    A[-1,n+1] = 1
    b[-1] = 1

    sol = A.solve_right(b)

    x = SR.var("x", QQ)
    return (
        sum( sol[i] * x**i for i in range(n + 1) ) /
        sum( sol[i+n+1] * x**i for i in range(n + 1) )
    )


if __name__ == "__main__":
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


