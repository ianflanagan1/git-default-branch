# git-default-branch

Tells which branch is a git repository's default: the one work is integrated into. Every tool that needs to know asks here, as a Python function or a command, so they all go by the same rules and none of them assumes the branch is called `main`.

```
$ git default-branch
main
```

Runs on macOS and Linux. Built on [cli-kit](https://github.com/ianflanagan1/cli-kit).

## How it decides

The sources are tried in order, and the first that says wins:

1. **`default-branch.name` in git config**, for a repository whose integration branch isn't its remote's default, such as git-flow's `develop`: `git config default-branch.name develop`.
2. **The branch the remote's `HEAD` points to**, as `refs/remotes/<remote>/HEAD` records it. Clone records it, and fetch does too from git 2.48 when it's missing. Set `remote.origin.followRemoteHEAD` to `always` to follow a rename on the remote.
3. **The remote itself**, asked with `git remote set-head <remote> --auto`, which records its answer for next time. Skipped with `--offline`, or `ask_remote=False`.
4. **`init.defaultBranch`**, when that branch exists.
5. **`main` or `master`**, when exactly one of them exists.

The remote is the only one, or `origin` among several. When nothing says which it is, the answer is "none", never a guess.

## From Python

```python
from git_default_branch import default_branch

branch = default_branch(repo, ask_remote=False)  # str, or None when it can't tell
```

`None` covers both "can't tell" and "not a repository": a caller can do the same with either. `read(repo, ask_remote)` gives the facts it went by, `choose(facts)` the decision, and `why_unknown(facts)` a reason for a person to read.

Depend on it from another tool with:

```toml
[tool.uv.sources]
git-default-branch = { path = "../git-default-branch", editable = true }
```

## From the command line

`git-default-branch [<repo>] [--offline]`, or `git default-branch`. It prints the branch alone, for scripts to read:

```sh
branch=$(git default-branch) || exit 1
```

When it can't tell, it prints nothing on stdout, says why on stderr and exits 1:

```
⚠️ Can't tell the default branch: there's no remote, and both main and master exist. Set it with: git config default-branch.name <branch>
```

## Setup

```sh
cd ~/projects/cli/git-default-branch
devbox run setup   # uv sync, then links git-default-branch into ~/.local/bin
```

## Development

```sh
devbox run check   # ruff, then pytest
```

## License

MIT
