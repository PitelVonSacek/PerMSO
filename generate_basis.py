#!/usr/bin/env python

from common import run_mona, read_up_to
from io import StringIO
from perms import GridGeomClass, jinja_env, number_to_perm, ensure_known_keys, KNOWN_KEYS
import re
import sys
from sage.all import *
import subprocess
import yaml

ACCEPT = object()


def parse_automaton(inp):
    read_up_to(inp, "Initial state: 0")
    final = list(map(int, read_up_to(inp, "Accepting states: ([0-9 ]+)")[1].split()))
    states = int(read_up_to(inp, "Automaton has ([0-9]+) states and [0-9]+ BDD-nodes")[1])

    G = DiGraph(states - 1, loops=True, multiedges=True)
    for f in final: G.set_vertex(f - 1, ACCEPT)

    assert next(inp).strip() == "Transitions:"
    for line in inp:
        line = line.strip()
        if line == "": break
        m = re.fullmatch("State ([0-9]+): ([01X]+) -> state ([0-9]+)", line)
        assert m, f"Failed to match line '{line}'"

        G.add_edge(int(m[1]) - 1, int(m[3]) - 1, m[2])

    return G


def all_paths(G, from_, to):
    return G.all_paths(from_, to, use_multiedges=True, report_edges=True, labels=True)


def path_to_points(C, path):
    n = C.n

    def label_to_block(label):
        assert 'X' not in label
        assert label.count('1') == 1
        return label.index('1')

    def edge_to_point(index, edge):
        b = C.blocks[label_to_block(edge[2])]
        return (
          2*n*b.col + C.col_signs[b.col]*index,
          2*n*b.row + C.row_signs[b.row]*index
        )

    return [ edge_to_point(i, e) for i, e in enumerate(path) ]


def points_to_perm(points):
    perm = [ y for _, y in sorted(points) ]
    m = { v: i for i, v in enumerate(sorted(perm)) }
    return tuple( m[y] + 1 for y in perm )


def extend_single_row(cls, i):
    cls_ext = [
        row + [ 1 if r == i else 0 ]
        for r, row in enumerate(cls)
    ]

    C = GridGeomClass(cls_ext)
    single = C.indices[C.rows - 1 - i][-1]

    mona = jinja_env.get_template(f"gridded_basis.mona").render(**{
        "class": cls_ext,
        "C": C,
        "single": single,
        "gridded": False,
        "avoid": [],
        "sum_indecomposable": False,
        "skew_indecomposable": False,
        "simple": False,
        "extra": "true",
        "class_extra": "true",
    })

    G = parse_automaton(StringIO(run_mona(mona)))

    for v in G.vertex_iterator():
        if G.get_vertex(v) is not ACCEPT: continue
        for p in all_paths(G, 0, v):
            yield points_to_perm(path_to_points(C, p))


def generate_basis(cls):
    cls = ensure_known_keys(cls)

    assert cls["type"] == "geom_grid", "Basis generation is supported only for geom. grid classes"
    for k, v in cls.items():
        if k in [ "type", "class" ] or k not in KNOWN_KEYS: continue
        assert v == KNOWN_KEYS[k], "Extra conditions are not supported for basis generation"

    cls = cls["class"]

    basis = set()
    for i in range(len(cls)):
        for p in extend_single_row(cls, i):
            basis.add(p)

    return basis


if __name__ == "__main__":
    cls = yaml.load(sys.stdin, Loader=yaml.SafeLoader)
    for p in sorted(generate_basis(cls), key=lambda p: (len(p), p)):
        print(p)

