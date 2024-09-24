#!/usr/bin/python

from sys import argv
import yaml

with open(argv[1], "r") as f:
    for t in yaml.load_all(f, Loader=yaml.SafeLoader):
        if not argv[2] or argv[2] == t.get("name", None):
            print(yaml.dump(t, default_flow_style=None))
            break
    else:
        print(f"Class '{argv[2]}' not found!")
        exit(1)

