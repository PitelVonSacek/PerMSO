#!/usr/bin/env python

import ast
import collections
import re
import sys

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

    def _def_order(self, below):
        R = range(len(self.blocks))
        def index(i):
            b = self.blocks[i]
            return b.row if below else b.col

        def cond(i, j):
            i_index = index(i)
            j_index = index(j)
            if i_index > j_index: return "false"
            if i_index < j_index: return "true"

            signs = self.row_signs if below else self.col_signs
            return "x < y" if signs[i_index] == 1 else "x > y"

        return " |\n  ".join(
            f"(x in A{i} & y in A{j} & { cond(i, j) })"
            for i in R for j in R
        )

    def _left_of(self): return self._def_order(False)
    def _below_of(self): return self._def_order(True)

    def _mon_prime_2(self):
        def ord_in(block):
            return "x, y" if block.sign == 1 else "y, x"

        return " &\n  ".join(
            f"(all1 x, y: (x in Y{i} & y in Y{i} & left_of(x, y)) => below_of({ord_in(b)}))"
            for i, b in enumerate(self.blocks)
        )

    def _mon_prime_3(self):
        return " &\n  ".join([
            f"(all1 x, y: (x in Y{i} & y in Y{j}) => left_of(x, y))"
            for i, C_i in enumerate(self.blocks)
            for j, C_j in enumerate(self.blocks)
            if C_i.col < C_j.col
        ] + [
            f"(all1 x, y: (x in Y{i} & y in Y{j}) => below_of(x, y))"
            for i, C_i in enumerate(self.blocks)
            for j, C_j in enumerate(self.blocks)
            if C_i.row < C_j.row
        ])

    def mona_description(self):
        l = len(self.blocks)
        def parts(templ, join=", "):
            return join.join( templ.format(i=i) for i in range(l) )
        def all_but(i):
            return " & ".join( f"x notin X{j}" for j in range(l) if i != j )
        contained_once = " &\n  ".join( f"(x in X{i} => {all_but(i)})" for i in range(l) )

        As = parts("A{i}")
        Xs = parts("X{i}")
        var_Xs = parts("var2 X{i}")
        Ys = parts("Y{i}")
        var_Ys = parts("var2 Y{i}")

        inorder_in_i = ";\n".join(
            f"pred below_in_{i}(var1 x, var2 y) = below_of({ord_})"
            for i in range(l) for ord_ in [ "x, y" if self.blocks[i].sign == 1 else "y, x" ]
        )

        M_formated = "\n".join( f"#   {row}" for row in reversed(self.M) )

        let_B = " ".join(
            f"let2 B{i+1} = B{i} union A{i} in" for i in range(l)
        )

        def independent_before(i):
            b = self.blocks[i]
            return " union ".join(
                f"A{i}" for j in range(i)
                if self.blocks[j].row != b.row and self.blocks[j].col != b.col
            ) or "{}"

        let_I = "\n  ".join(
            f"let2 I{i} = { independent_before(i) } in" for i in range(l)
        )

        trace_min = " &\n    ".join(
            f"(x - 1 in A{i} => x notin I{i})" for i in range(l)
        )

        return re.sub("\n" + " "*12, "\n", f"""
            # Generated by perms.py
            # version: { VERSION }
            #
            # Input matrix:
            { M_formated }
            #
            # Computed row signs: { list(reversed(self.row_signs)) }
            # Computed col signs: { self.col_signs }

            m2l-str;

            var2 {As};

            pred partition({var_Xs}) = all1 x:
              ({ parts('x in X{i}', ' | ') }) &
              {contained_once};

            pred left_of(var1 x, var1 y) =
              {self._left_of()};

            pred below_of(var1 x, var1 y) =
              {self._below_of()};

            pred Mon'({var_Ys}) =
              partition({Ys}) &
              {self._mon_prime_2()} &
              {self._mon_prime_3()};

            pred bigger_than_A({var_Ys}) = ex1 x:
              let2 B0 = empty in {let_B}
              # x is earlier in As than in Ys
              { parts('(x in Y{i} => x in B{i})', ' & ') } &
              # and all elements left of x are the same in As and Ys
              (all1 y: left_of(y, x) => ({ parts('(y in A{i} <=> y in Y{i})', ' & ') }));

            pred different({var_Xs}, {var_Ys}) =
              { parts('X{i} ~= Y{i}', ' | ') };

            pred minimal_gridding() = all2 {Ys}:
              Mon'({Ys}) & different({As}, {Ys})
              => bigger_than_A({Ys});

            pred trace_min() = all1 x: x > 0 =>
              {let_I} (
                {trace_min}
              );

            partition({As}) & minimal_gridding() & trace_min();
        """).strip()


if __name__ == "__main__":
    C = GridGeomClass(ast.literal_eval(sys.stdin.read()))
    print(C.mona_description())

