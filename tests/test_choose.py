"""Behaviour of choosing the default branch from what a repository says about it."""

from git_default_branch import Facts, choose, needs_remote, remote_to_ask, why_unknown


def facts() -> Facts:
    """A repository that says nothing about its default branch: no override, no remote, no
    init.defaultBranch and no branches."""
    return Facts(override=None, remote=None, remote_head=None, init_default=None, branches=())


def with_(base: Facts, **changes) -> Facts:
    return Facts(**{**base.__dict__, **changes})


# --- The order the sources are tried in


def test_the_override_in_git_config_wins_over_everything_else():
    repo = with_(
        facts(),
        override="develop",
        remote="origin",
        remote_head="main",
        init_default="main",
        branches=("main",),
    )
    assert choose(repo) == "develop"


def test_the_branch_the_remotes_head_points_to_comes_next():
    repo = with_(facts(), remote="origin", remote_head="trunk", branches=("main",))
    assert choose(repo) == "trunk"


def test_without_the_remotes_word_init_default_branch_is_used_when_that_branch_exists():
    repo = with_(facts(), init_default="trunk", branches=("master", "trunk"))
    assert choose(repo) == "trunk"


def test_init_default_branch_is_skipped_when_there_is_no_such_branch():
    repo = with_(facts(), init_default="trunk", branches=("master",))
    assert choose(repo) == "master"


def test_as_a_last_resort_main_is_the_default_when_it_is_the_only_one_of_main_and_master():
    assert choose(with_(facts(), branches=("feature", "main"))) == "main"


def test_as_a_last_resort_master_is_the_default_when_it_is_the_only_one_of_main_and_master():
    assert choose(with_(facts(), branches=("feature", "master"))) == "master"


# --- Not guessing


def test_with_both_main_and_master_and_nothing_else_to_go_on_it_is_unknown():
    assert choose(with_(facts(), branches=("main", "master"))) is None


def test_with_neither_main_nor_master_and_nothing_else_to_go_on_it_is_unknown():
    assert choose(with_(facts(), branches=("feature",))) is None


def test_a_repository_with_no_branches_has_no_default_branch():
    assert choose(facts()) is None


# --- Which remote to ask


def test_the_only_remote_is_the_one_asked():
    assert remote_to_ask(["upstream"]) == "upstream"


def test_with_several_remotes_origin_is_asked():
    assert remote_to_ask(["fork", "origin"]) == "origin"


def test_with_several_remotes_and_none_named_origin_none_is_asked():
    assert remote_to_ask(["fork", "upstream"]) is None


def test_with_no_remote_none_is_asked():
    assert remote_to_ask([]) is None


def test_the_remote_is_asked_only_when_neither_the_override_nor_its_head_says():
    assert needs_remote(with_(facts(), remote="origin"))
    assert not needs_remote(with_(facts(), remote="origin", remote_head="main"))
    assert not needs_remote(with_(facts(), remote="origin", override="develop"))
    assert not needs_remote(facts())


# --- Saying why it's unknown


def test_why_says_both_main_and_master_exist_and_how_to_choose():
    reason = why_unknown(with_(facts(), branches=("main", "master")))
    assert reason == (
        "Can't tell the default branch: there's no remote, and both main and master exist. "
        "Set it with: git config default-branch.name <branch>"
    )


def test_why_says_the_remote_named_no_default_branch():
    reason = why_unknown(with_(facts(), remote="origin", branches=("feature",)))
    assert reason == (
        "Can't tell the default branch: origin doesn't name one, and neither main nor master "
        "exists. Set it with: git config default-branch.name <branch>"
    )
