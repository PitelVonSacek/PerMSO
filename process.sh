#!/bin/bash

save() {
  if [[ -n "$1" ]]; then
    cat > "$1"
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

mona_desc="$(
  ./perms.py <<<"$inp"
)"

save "$MONA" <<<"$mona_desc"

[[ -n "$MONA_STATS" ]] && MONA_FLAGS=-s || MONA_FLAGS=

automaton="$(
  mona $MONA_FLAGS -w /dev/stdin <<<"$mona_desc"
)"

if ! grep -q ANALYSIS <<<"$automaton"; then
  tail -n1 <<<"$automaton"
  echo ""
  echo "MONA failed!"
  exit 1
fi

save "$AUTOMATON" <<<"$automaton"

sol=$(
  ./process_automaton.py "$MATRIX" <<<"$automaton"
)

echo "$sol"

if [[ -n "$EXPAND" ]]; then
  python <<<"if True:
    from sage.all import *
    var('x')
    print(SR('$sol').series(x, $EXPAND))
  "
fi

