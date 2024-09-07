#!/usr/bin/env python

from io import StringIO
import re
import os
import subprocess
import sys
import yaml

from sage.all import *

from perms import gen_mona
from process_automaton import parse_automaton, automaton_to_generating_function as a2gf

DIR = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")


def run_mona(mona_desc):
    return subprocess.check_output([ "mona", "-w", "/dev/stdin" ],
        encoding="utf-8", input=mona_desc, shell=False)


def log(*args, **kwargs):
    print(*args, **kwargs, end="", flush=True)


if __name__ == "__main__":
    test_file = sys.argv[1] if len(sys.argv) >= 2 else f"{DIR}/tests.yaml"

    with open(test_file, "r") as f:
        tests = list(yaml.load_all(f, Loader=yaml.SafeLoader))

    skipped = 0
    for t in tests:
        log(f"{t['name']}:")
        mona = gen_mona(t)
        if t.get("skip", False):
          log(f"Skipping ({t['skip']})\n")
          skipped += 1

        res = a2gf(*parse_automaton(StringIO(run_mona(mona))))

        if "gen_fun" in t:
            log(" gen_fun ")
            ref = SR(t["gen_fun"])
            if (ref - res).simplify_full() != 0:
                log(f"\nFailed: expected {ref} but got {res}\n")
                exit(1)
            log("ok")

        if "first_values" in t:
            log(" values ")
            x = res.variables()[0]
            s = res.series(x, len(t["first_values"]))
            for i, ref_val in enumerate(t["first_values"]):
                val = s.coefficient(x, i)
                if ref_val != val:
                    log(f"\nFailed on value {i}: expected {ref_val} but got {val}\n")
                    exit(1)
            log("ok")

        log("\n")

    skipped = f" ({skipped} skipped)" if skipped else ""
    log(f"All tests succeded{skipped}.\n")

