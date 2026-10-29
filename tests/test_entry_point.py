"""The git-default-branch command that uv installs into .venv/bin."""

import os
import subprocess
import sys
from pathlib import Path

BIN = Path(sys.prefix) / "bin" / "git-default-branch"


def launch(*args: str | Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [BIN, *map(str, args)], capture_output=True, text=True, cwd=cwd, env=os.environ.copy()
    )


def test_it_prints_the_default_branch_alone_for_scripts_to_read(repos):
    clone = repos.clone(repos.repo("origin", "trunk"), "clone")
    result = launch(cwd=clone)
    assert (result.returncode, result.stdout, result.stderr) == (0, "trunk\n", "")


def test_it_reads_the_repository_given_rather_than_the_current_one(repos, tmp_path: Path):
    clone = repos.clone(repos.repo("origin", "trunk"), "clone")
    result = launch(clone, cwd=tmp_path)
    assert (result.returncode, result.stdout) == (0, "trunk\n")


def test_when_it_cannot_tell_it_prints_nothing_and_says_why_on_stderr(repos):
    repo = repos.repo("repo", "main")
    repos.git("-C", repo, "branch", "master")
    result = launch(cwd=repo)
    assert (result.returncode, result.stdout) == (1, "")
    assert result.stderr == (
        "⚠️ Can't tell the default branch: there's no remote, and both main and master exist. "
        "Set it with: git config default-branch.name <branch>\n"
    )


def test_offline_it_does_not_ask_the_remote(repos):
    origin = repos.repo("origin", "trunk")
    clone = repos.clone(origin, "clone")
    repos.git("-C", clone, "remote", "set-head", "origin", "--delete")
    repos.git("-C", clone, "branch", "--move", "trunk", "main")
    assert launch("--offline", cwd=clone).stdout == "main\n"
    assert launch(cwd=clone).stdout == "trunk\n"


def test_outside_a_repository_it_says_so(tmp_path: Path):
    result = launch(cwd=tmp_path)
    assert (result.returncode, result.stdout) == (1, "")
    assert result.stderr == f"⚠️ Not a git repository: {tmp_path.resolve()}\n"


def test_git_runs_it_as_a_subcommand(repos, tmp_path: Path):
    clone = repos.clone(repos.repo("origin", "trunk"), "clone")
    env = os.environ | {"PATH": f"{BIN.parent}{os.pathsep}{os.environ['PATH']}"}
    result = subprocess.run(
        ["git", "default-branch"], capture_output=True, text=True, cwd=clone, env=env
    )
    assert result.stdout == "trunk\n"
