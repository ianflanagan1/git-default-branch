"""Behaviour of reading a real repository's default branch."""

from pathlib import Path

from git_default_branch import default_branch


def test_a_clone_takes_the_default_branch_its_origin_has(repos):
    origin = repos.repo("origin", "trunk")
    repos.git("-C", origin, "branch", "main")
    clone = repos.clone(origin, "clone")
    assert default_branch(clone, ask_remote=False) == "trunk"


def test_the_override_in_git_config_wins_over_the_remote(repos):
    clone = repos.clone(repos.repo("origin", "main"), "clone")
    repos.git("-C", clone, "config", "default-branch.name", "develop")
    assert default_branch(clone, ask_remote=False) == "develop"


def test_a_remote_whose_head_is_not_recorded_is_asked_and_its_answer_kept(repos):
    origin = repos.repo("origin", "trunk")
    clone = repos.clone(origin, "clone")
    repos.git("-C", clone, "remote", "set-head", "origin", "--delete")
    repos.git("-C", clone, "branch", "-m", "trunk", "main")
    assert default_branch(clone, ask_remote=True) == "trunk"
    assert repos.git("-C", clone, "symbolic-ref", "refs/remotes/origin/HEAD") == (
        "refs/remotes/origin/trunk"
    )


def test_without_asking_the_remote_the_local_branches_are_gone_by(repos):
    origin = repos.repo("origin", "trunk")
    clone = repos.clone(origin, "clone")
    repos.git("-C", clone, "remote", "set-head", "origin", "--delete")
    repos.git("-C", clone, "branch", "-m", "trunk", "main")
    assert default_branch(clone, ask_remote=False) == "main"


def test_a_remote_that_cannot_be_reached_falls_back_to_the_local_branches(repos, tmp_path: Path):
    repo = repos.repo("repo", "master")
    repos.git("-C", repo, "remote", "add", "origin", tmp_path / "gone.git")
    assert default_branch(repo, ask_remote=True) == "master"


def test_without_a_remote_init_default_branch_is_used_when_that_branch_exists(repos):
    repo = repos.repo("repo", "master")
    repos.git("-C", repo, "branch", "trunk")
    repos.git("config", "--global", "init.defaultBranch", "trunk")
    assert default_branch(repo, ask_remote=False) == "trunk"


def test_with_both_main_and_master_and_nothing_else_to_go_on_there_is_none(repos):
    repo = repos.repo("repo", "main")
    repos.git("-C", repo, "branch", "master")
    assert default_branch(repo, ask_remote=False) is None


def test_a_folder_that_is_not_a_repository_has_none(tmp_path: Path):
    assert default_branch(tmp_path, ask_remote=False) is None


def test_a_linked_worktree_has_the_same_default_branch_as_its_main_checkout(repos, tmp_path):
    clone = repos.clone(repos.repo("origin", "trunk"), "clone")
    worktree = tmp_path / "clone-wt1"
    repos.git("-C", clone, "worktree", "add", "-q", "--detach", worktree)
    assert default_branch(worktree, ask_remote=False) == "trunk"
