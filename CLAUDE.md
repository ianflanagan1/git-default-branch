# git-default-branch

`devbox run -- task check` runs ruff and the tests; run it before finishing. `devbox run -- task lint-file -- <files>` formats and fixes the Python files given.

The decision is `choose`, a pure function of `Facts`; keep git out of it, and test it with plain values in `tests/test_choose.py`. `read` and the command are the shell, covered by tests against real throwaway repositories.
