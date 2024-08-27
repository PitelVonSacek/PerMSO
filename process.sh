#!/bin/bash

save() {
  if [[ -n "$1" ]]; then
    tee "$1"
  else
    cat
  fi
}

sol=$(
  ./perms.py |
  save "$MONA" |
  mona -w /dev/stdin |
  save "$AUTOMATON" |
  ./process_automaton.py "$MATRIX"
)

echo "$sol"

if [[ -n "$EXPAND" ]]; then
  python <<<"if True:
    from sage.all import *
    var('x')
    print(SR('$sol').series(x, $EXPAND))
  "
fi

