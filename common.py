from os import environ
import re
import subprocess
from sys import argv


def try_log(logfile, fun):
    if logfile is None: return
    with open(logfile, "a") as f:
        print(fun(), file=f)


MONA_CMD = environ.get("MONA_CMD", "mona").split()
MONA_IN_LOG = environ.get("MONA_IN_LOG", None)
MONA_OUT_LOG = environ.get("MONA_OUT_LOG", None)

def run_mona(mona_desc, need_automaton=True):
    cmd = list(MONA_CMD)
    if need_automaton: cmd += [ "-u", "-w" ]
    cmd += [ "/dev/stdin" ]

    try_log(MONA_IN_LOG, lambda: f">>> {cmd}\n{mona_desc}\n")

    ret = subprocess.check_output(cmd,
        encoding="utf-8", input=mona_desc, shell=False)

    try_log(MONA_OUT_LOG, lambda: f">>> {cmd}\n{ret}\n")

    return ret


def read_up_to(inp, expr):
    for line in inp:
        m = re.fullmatch(expr, line.strip())
        if m: return m

    raise Exception("Failed to match expr")

