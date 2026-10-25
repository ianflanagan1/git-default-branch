"""Print the default branch of a git repository: the one work is integrated into.

Tries, in order: default-branch.name in git config; the branch the remote's HEAD points to, as
recorded; the remote itself, asked over the network and its answer recorded (not with
--offline); init.defaultBranch, when that branch exists; and main or master, when exactly one of
them exists. The remote is the only one, or origin among several.

Prints the branch alone, for scripts to read. When nothing says which it is, it prints nothing,
says why on stderr and exits 1: it never guesses. Git also runs it as `git default-branch`.

Exit status: 0 printed the branch, 1 couldn't tell or not a repository, 2 usage error.
"""

import sys
from pathlib import Path

from cli_kit import cli

from git_default_branch import choose, read, why_unknown


def main(argv: list[str] | None = None) -> int:
    parser = cli.ArgumentParser(prog="git-default-branch", description=__doc__)
    parser.add_argument("repo", nargs="?", default=".", help="default: the current directory")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="don't ask the remote when its HEAD isn't recorded",
    )
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()

    facts = read(repo, ask_remote=not args.offline)
    if facts is None:
        print(f"⚠️ Not a git repository: {repo}", file=sys.stderr)
        return 1
    branch = choose(facts)
    if branch is None:
        print(f"⚠️ {why_unknown(facts)}", file=sys.stderr)
        return 1
    print(branch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
