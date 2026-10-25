"""Which branch is a git repository's default: the one work is integrated into.

Every tool that needs to know asks here, so they all agree. The sources are tried in this order:

1. The override in git config, `default-branch.name`, for a repository whose integration branch
   isn't its remote's default, such as git-flow's develop.
2. The branch the remote's HEAD points to, as `refs/remotes/<remote>/HEAD` records it. Clone
   records it, and so does fetch, from git 2.48, when it's missing.
3. The remote itself, asked with `git remote set-head <remote> --auto`, which also records its
   answer for next time. Only when the caller allows the network.
4. init.defaultBranch, when that branch exists.
5. main or master, when exactly one of them exists.

Otherwise there's no telling, and the answer is None: never a guess.

The remote is the only one, or origin when there are several.
"""

import os
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import final

OVERRIDE = "default-branch.name"
ORIGIN = "origin"
LAST_RESORTS = ("main", "master")
SET_HEAD_TIMEOUT_SECONDS = 30


@final
@dataclass(frozen=True)
class Facts:
    """What a repository says about its default branch."""

    override: str | None
    """The branch named by default-branch.name in git config."""
    remote: str | None
    """The remote to go by, or None when there's none to choose."""
    remote_head: str | None
    """The branch the remote's HEAD points to, as last recorded."""
    init_default: str | None
    """init.defaultBranch in git config."""
    branches: Sequence[str]
    """The local branches."""


def choose(facts: Facts) -> str | None:
    """The default branch, or None when nothing says which it is."""
    if facts.override:
        return facts.override
    if facts.remote_head:
        return facts.remote_head
    if facts.init_default and facts.init_default in facts.branches:
        return facts.init_default
    found = [name for name in LAST_RESORTS if name in facts.branches]
    return found[0] if len(found) == 1 else None


def remote_to_ask(remotes: Sequence[str]) -> str | None:
    """The remote whose HEAD names the default branch: the only one, or origin among several."""
    if len(remotes) == 1:
        return remotes[0]
    return ORIGIN if ORIGIN in remotes else None


def needs_remote(facts: Facts) -> bool:
    """Whether only asking the remote could say more than is recorded."""
    return facts.override is None and facts.remote_head is None and facts.remote is not None


def why_unknown(facts: Facts) -> str:
    """Why choose found no default branch, and how to set one, for a person to read."""
    remote = f"{facts.remote} doesn't name one" if facts.remote else "there's no remote"
    found = [name for name in LAST_RESORTS if name in facts.branches]
    branches = "both main and master exist" if len(found) == 2 else "neither main nor master exists"
    return (
        f"Can't tell the default branch: {remote}, and {branches}. "
        f"Set it with: git config {OVERRIDE} <branch>"
    )


def read(repo: Path, ask_remote: bool) -> Facts | None:
    """What repo says about its default branch, or None when it isn't a repository.

    With ask_remote, a remote whose HEAD isn't recorded is asked, and its answer recorded.
    """
    if _git(repo, "rev-parse", "--git-dir") is None:
        return None
    facts = _read(repo)
    if ask_remote and needs_remote(facts) and facts.remote:
        _ask(repo, facts.remote)
        facts = _read(repo)
    return facts


def default_branch(repo: Path, ask_remote: bool) -> str | None:
    """repo's default branch, or None when nothing says which it is or repo isn't a repository.

    With ask_remote, a remote whose HEAD isn't recorded is asked over the network.
    """
    facts = read(repo, ask_remote)
    return choose(facts) if facts else None


def _read(repo: Path) -> Facts:
    remote = remote_to_ask((_git(repo, "remote") or "").splitlines())
    head = _git(repo, "symbolic-ref", "-q", "--short", f"refs/remotes/{remote}/HEAD")
    return Facts(
        override=_git(repo, "config", "--get", OVERRIDE),
        remote=remote,
        remote_head=head.removeprefix(f"{remote}/") if remote and head else None,
        init_default=_git(repo, "config", "--get", "init.defaultBranch"),
        branches=(
            _git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads") or ""
        ).splitlines(),
    )


def _ask(repo: Path, remote: str) -> None:
    """Asks remote which branch its HEAD points to and records it. A remote that can't be
    reached, or wants a password, leaves nothing recorded."""
    try:
        subprocess.run(
            ["git", "-C", str(repo), "remote", "set-head", remote, "--auto"],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            env=_batch_env(),
            timeout=SET_HEAD_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        pass


def _git(repo: Path, *args: str) -> str | None:
    """git's output in repo, stripped, or None when it fails."""
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, stdin=subprocess.DEVNULL
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _batch_env() -> dict[str, str]:
    return os.environ | {
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_SSH_COMMAND": os.environ.get("GIT_SSH_COMMAND", "ssh") + " -o BatchMode=yes",
    }
