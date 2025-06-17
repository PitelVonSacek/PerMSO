# Permutation enumeration tools

This repository contains tools to enumerate specific permutation classes
and test files containing known results.

NOTE: We exclude the permutation of the length zero.


## Idea

The overall approach is to create a WS1S formula such that there is a bijection
between models satisfying this formula and permutations from the permutation class
of interest and moreover this bijection preserves size, i.e., for permutation
of `k` elements, the corresponding model has integers 0 up to `k - 1` as its
objects. Then we use MONA to transform the formula into finite automaton such
that accepted strings are in bijection with the models (again preserving size),
and hence by transitivity with permutations. Finally we use SageMath to solve
a system of linear equations obtained from the automaton to get a generating
function of the number of accepted strings of length `k`.

Currently we support acyclic grid classes and insertion encoding plus we can
restrict the class by any condition expressed in WS1S. We have prepared conditions
for sum-/skew-indecomposable, simple permutations, and avoidance of specified
permutations.


## Tools

- `contains.py`: Tests if given permutation is a member of given
  class. The permutation is the first argument. Class may be specified
  either by the two following arguments (name of yaml file and name
  of the class in the file) or by yaml description read from standard
  input.

- `generate_basis.py`: Calculates the basis of given class. It currently
  supports only geometric grid classes without any extra conditions.

- `get_class.py`: Takes yaml filename and optionally a name of class in the
  file and prints the description of corresponding class. Prints the first
  class in the file if no class name is given.

- `perms.py` reads a description of a class from standard input
  and prints MONA input file on standard output.

- `parse_automaton.py` reads automaton outputted by MONA and attempts
  to calculate generating function of accepted words. The generating
  function is calculated by solving system of linear equations.
  This requires SageMath installed.

- `process.sh` reads class description from standard input and
  prints generation function on standard output. Internally
  it just calls `perms.py`, MONA and `parse_automaton.py`.
  Recognized environment variables:

  - `MONA`: File to save class description in MONA language.
  - `MONA_CMD`: Command to launch MONA (`ssh server mona` might
    be used to run MONA on a different machine; default value is
    `mona`).
  - `MONA_STATS`: If non-empty, add `-s` to MONA invocation.
  - `AUTOMATON`: File to save the automaton.
  - `EXPAND`: Calculate the number of permutations for all lengths
    up to `EXPAND`.

- `run_tests.py`: Runs all tests specified in given yaml files (uses
  `tests.yaml` in its directory if no files are given). Options are:
  
  - `-b`, `--skip-basis`: Whether to skip basis generation. Possible
    values are `on` (always skip), `off` (never skip), `auto` (skip
    if `skip_basis` is true for given class).
  - `-e`, `--skip-expr`: An arbitrary Python expression to be run
    on class description. It it evaluates to true, this class is
    skipped during testing. Defaults to value of `skip` key.
  - `-f`, `--start-from`: Skip testing all classes before the class
    with the name given as argument to this option.


## Class description

A permutation class is described as `yaml` object with keys:

- `type`: The type of the class. We currently support `geom_grid`
  and `insertion_enc` (`geom_grid` is the default value).
- `class`: The description of the class. It is a matrix (list of
  lists) containing 1, -1 and 0 for `geom_grid` and an integer
  denoting the number of insertion points for `insertion_enc`.
- `gridded`: Boolean, for `geom_grid` only. If `true`, do not
  factorize by different griddings of one permutation.
- `sum_indecomposabe`: Boolean whether restrict the class to only
  sum indecomposable permutations.
- `skew_indecomposabe`: Boolean whether restrict the class to only
  skew indecomposable permutations.
- `simple`: Boolean whether restrict the class to only simple
  permutations.
- `extra`: Formula which permutations must satisfy apart from all
  other. It should not refer the representation of the permutation.
- `class_extra`: Like `extra` but it might use the class specific
  representation.

Extra keys supported in test files:

- `name`: Name of the class.
- `gen_fun`: The generating function.
- `first_values`: List of the number of permutations it the class
  for lengths up to some `k`. Including 0 for permutations of
  zero length.
- `basis`: The basis of the class as list of permutations. Each
  permutation can be written as either a single integer or sequence
  of integers.
- `skip`: Evaluated as boolean. If true, skip this class when running tests.
- `skip_basis`: Boolean, it true, skip basis calculation for this class
  even thought `basis` key is present.

