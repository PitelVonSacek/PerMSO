#!/usr/bin/env python

from common import run_mona
from io import StringIO
import re
import os
import subprocess
import sys
import yaml

from sage.all import *

from generate_basis import generate_basis, number_to_perm
from perms import gen_mona
from process_automaton import parse_automaton, automaton_to_generating_function as a2gf

DIR = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")


def log(*args, **kwargs):
    print(*args, **kwargs, end="", flush=True)


class TestFailed(Exception):
  pass


def run_test_file(test_file, skip_basis=False):
    with open(test_file, "r") as f:
        tests = list(yaml.load_all(f, Loader=yaml.SafeLoader))

    skipped = 0
    mona_failed = 0
    for t in tests:
        log(f"{t['name']}:")
        mona = gen_mona(t)
        if t.get("skip", False):
            log(f" Skipping ({t['skip']})\n")
            skipped += 1
            continue

        try:
            automaton = run_mona(mona)
        except subprocess.CalledProcessError as e:
            mona_failed += 1
            log(f" Mona failed: {e}\n")
            continue

        res = a2gf(*parse_automaton(StringIO(automaton)))

        if "gen_fun" in t:
            log(" gen_fun ")
            ref = SR(t["gen_fun"])
            if (ref - res).simplify_full() != 0:
                log(f"\nFailed: expected {ref} but got {res}\n")
                raise TestFailed()
            log("ok")

        if "first_values" in t:
            log(" values ")
            x = res.variables()[0]
            s = res.series(x, len(t["first_values"]))
            for i, ref_val in enumerate(t["first_values"]):
                val = s.coefficient(x, i)
                if ref_val != val:
                    log(f"\nFailed on value {i}: expected {ref_val} but got {val}\n")
                    raise TestFailed()
            log("ok")

        if not skip_basis and "basis" in t:
            log(" basis ")
            if t.get("skip_basis", False):
                log("skipped\n")
                skipped += 1
                continue

            ref = {
                tuple(x) if isinstance(x, list) else number_to_perm(x)
                for x in t["basis"]
            }
            try:
                b = generate_basis(t["class"])
            except subprocess.CalledProcessError as e:
                log(f" Mona failed (basis): {e}\n")
                continue

            if ref != b:
                log(f"\nFailed: got basis {b} but expected {ref}\n")
                raise TestFailed()
            log("ok")

        log("\n")

    return (skipped, mona_failed)


def get(l, i):
    return l[i] if len(l) > i else None


if __name__ == "__main__":
    first = 1
    skip_basis = False
    if get(sys.argv, 1) == "--skip-basis":
        skip_basis = True
        first += 1

    test_files = sys.argv[first:]
    if not test_files: test_files = [ f"{DIR}/tests.yaml" ]

    skipped = 0
    mona_failed = 0
    try:
        for f in test_files:
            s, m = run_test_file(f, skip_basis)
            skipped += s
            mona_failed += m
    except TestFailed:
        exit(1)

    if mona_failed:
        log(f"Mona failed {mona_failed} times.\n")
    else:
        skipped = f" ({skipped} skipped)" if skipped else ""
        log(f"All tests succeded{skipped}.\n")

