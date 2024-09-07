#!/bin/bash

save() {
  if [[ -n "$1" ]]; then
    tee "$1"
  else
    cat
  fi
}

if [[ -n "$1" ]]; then
  get_test='if True:
    from sys import argv
    import yaml

    with open(argv[1], "r") as f:
        for t in yaml.load_all(f, Loader=yaml.SafeLoader):
            if not argv[2] or argv[2] == t.get("name", None):
                print(yaml.dump(t))
                break
  '

  inp="$(python -c "$get_test" "$1" "$2")"
else
  inp="$(cat)"
fi

sol=$(
  ./perms.py <<<"$inp" |
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

