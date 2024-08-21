#!/bin/bash

save() {
  if [[ -n "$1" ]]; then
    tee "$1"
  else
    cat
  fi
}

./perms.py |
save "$MONA" |
mona -w /dev/stdin |
save "$AUTOMATON" |
./process_automaton.py "$MATRIX"

