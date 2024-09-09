import re
import subprocess
from os import environ

MONA_CMD = environ.get("MONA_CMD", "mona").split()

def run_mona(mona_desc):
    return subprocess.check_output(MONA_CMD + [ "-w", "/dev/stdin" ],
        encoding="utf-8", input=mona_desc, shell=False)


def read_up_to(inp, expr):
    for line in inp:
        m = re.fullmatch(expr, line.strip())
        if m: return m

    raise Exception("Failed to match expr")

