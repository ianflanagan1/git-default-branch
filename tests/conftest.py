"""Fixtures shared by the tests.

Every test starts with HOME pointed inside its temporary directory, so no real git config is
read, and git's init.defaultBranch unset.
"""

import subprocess
from pathlib import Path

import pytest


def git(*args: str | Path) -> str:
    return subprocess.run(
        ["git", *map(str, args)], check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture(autouse=True)
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("NO_COLOR", "1")
    git("config", "--global", "user.name", "test")
    git("config", "--global", "user.email", "test@example.com")
    git("config", "--global", "commit.gpgsign", "false")
    return home


class Repos:
    git = staticmethod(git)

    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path

    def repo(self, name: str, branch: str) -> Path:
        """A repository with one commit, on branch."""
        repo = self.tmp_path / name
        git("init", "-q", "-b", branch, repo)
        git("-C", repo, "commit", "-q", "--allow-empty", "-m", "init")
        return repo

    def clone(self, origin: Path, name: str) -> Path:
        clone = self.tmp_path / name
        git("clone", "-q", origin, clone)
        return clone


@pytest.fixture
def repos(tmp_path: Path) -> Repos:
    return Repos(tmp_path)
