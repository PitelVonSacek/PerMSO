#!/usr/bin/python

import yaml
import collections
import jinja2
import os
import sys

DIR = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(DIR))


from sage.all import *

VERSION = "unknown"

GridBlock = collections.namedtuple("GridBlock", "row col sign neighs")

class GridGeomClass:
    def __init__(self, M):
        self.M = list(reversed(M)) # stored with reversed rows so row 0 is at bottom
        self.rows = len(M)
        self.cols = len(M[0])

        self.indices, self.blocks = self._get_blocks()
        self.row_signs, self.col_signs = self._get_signs()
        self.n = len(self.blocks)

    def _get_blocks(self):
        indices = []
        blocks = []

        for r, row in enumerate(self.M):
            indices.append([])
            for c, val in enumerate(row):
                if val == 0:
                    indices[-1].append(None)
                    continue
                indices[-1].append(len(blocks))
                blocks.append(GridBlock(r, c, self.M[r][c], []))
        
        # find neighbors
        for r, c, s, N in blocks:
            for dr, dc in [ (1, 0), (-1, 0), (0, 1), (0, -1) ]:
                nr = r + dr
                nc = r + dc
                while 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if indices[nr][nc] is not None:
                        N.append(indices[nr][nc])
                        break
                    nr += dr
                    nc += dc

        return indices, blocks

    def _get_signs(self):
        P = MixedIntegerLinearProgram()
        # 1 -> 1; 0 -> -1
        r = P.new_variable(binary=True, indices=range(self.rows))
        c = P.new_variable(binary=True, indices=range(self.cols))

        for b in self.blocks:
            if b.sign == 1:
                P.add_constraint(r[b.row] == c[b.col])
            else:
                P.add_constraint(r[b.row] + c[b.col] == 1)

        # prefer 1 over -1
        P.set_objective(
          P.sum( r[i] for i in range(self.rows) ) +
          P.sum( c[i] for i in range(self.cols) )
        )
        P.solve()

        def get_values(var):
            vals = P.get_values(var, convert=bool, tolerance=1e-3)
            return [ 1 if v else -1 for _, v in sorted(vals.items()) ]

        rs, cs = get_values(r), get_values(c)
        for b in self.blocks:
            assert b.sign == rs[b.row]*cs[b.col]

        return rs, cs


def number_to_perm(x):
    if isinstance(x, list): return x

    l = []
    while x:
        l.append(x % 10)
        x //= 10

    return tuple(reversed(l))


TYPES = {
    "geom_grid": (GridGeomClass, "gridded"),
    "insertion_enc": (lambda x: x, "insertion_enc"),
}


KNOWN_KEYS = {
    "type": "geom_grid",
    "class": None,
    "gridded": False,
    "avoid": [],
    "sum_indecomposable": False,
    "skew_indecomposable": False,
    "simple": False,
    "extra": "true",
    "class_extra": "true",
}


IGNORED_KEYS = {
  "name", "gen_fun", "first_values", "skip", "basis", "skip_basis",
}


def ensure_known_keys(desc, warn_on_unknown=True):
    desc = dict(desc)

    if warn_on_unknown:
        for k in desc.keys():
            if k not in KNOWN_KEYS and k not in IGNORED_KEYS:
                print(f"WARNING: unknown key '{k}'", file=sys.stderr)

    for k, v in KNOWN_KEYS.items():
        if k not in desc:
            desc[k] = v

    desc["avoid"] = [ number_to_perm(x) for x in desc["avoid"] ]

    return desc


def gen_mona(desc, check_is_contained=None):
    desc = ensure_known_keys(desc, True)

    constructor, templ = TYPES[desc["type"]]
    desc |= {
        "check_is_contained": check_is_contained,
        "C": constructor(desc["class"]),
        "version": VERSION
    }

    return jinja_env.get_template(f"{templ}.mona").render(**desc)


if __name__ == "__main__":
    desc = yaml.load(sys.stdin, Loader=yaml.SafeLoader)
    print(gen_mona(desc))

