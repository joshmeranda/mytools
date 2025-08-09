import pathlib
import os
import subprocess
import git
import pytest
import datetime

_REPO_MANAGER_TIMEOUT: int = 10
_REPO_MANAGER_PATH: str = os.path.abspath("common/repo-manager.bash")

_ENV_CONFIG: str = "CONFIG"
_ENV_GITHUB_REGISTRY: str = "GITHUB_REGISTRY"
_ENV_SSH_USER: str = "SSH_USER"
_ENV_REPO_ROOT: str = "REPO_ROOT"
_ENV_CLEAN_AFTER: str = "CLEAN_AFTER"
_ENV_DEFAULT_CLONE_PROTO: str = "DEFAULT_CLONE_PROTO"
_ENV_DO_NOT_CLEAN: str = "DO_NOT_CLEAN"


def _assert_repo(path: pathlib.Path, expected_remotes: dict[str, str] = None):
	assert path.exists()

	repo = git.Repo(path)
	remotes = { remote.name: remote for remote in repo.remotes}

	if expected_remotes is not None:
		for expected_name, expected_url in expected_remotes.items():
			assert expected_name in remotes
			assert expected_url == remotes[expected_name].url


class TestConfig:
	def test_show_config(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "--show-config"],
			env={
				_ENV_REPO_ROOT: tmp_path,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert str.encode(f"     GITHUB_REGISTRY: github.com\n            SSH_USER: git\n           REPO_ROOT: {tmp_path}\n         CLEAN_AFTER: 28\n DEFAULT_CLONE_PROTO: ssh\n        DO_NOT_CLEAN: \n") == proc.stdout

	def test_show_config_with_non_default_file(self, tmp_path: pathlib.Path):
		config_file = tmp_path / "config"
		repo_root = tmp_path  / "repos"

		config_file.write_text(f"GITHUB_REGISTRY=some.custom.registry.com\nSSH_USER=bbaggins\nREPO_ROOT={repo_root}\nCLEAN_AFTER=7\nDEFAULT_CLONE_PROTO=https\nDO_NOT_CLEAN=joshmeranda/mytools,joshmeranda/fan")

		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "--show-config"],
			env={
				_ENV_REPO_ROOT: tmp_path / "repos",
				_ENV_CONFIG: config_file,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT
		)

		assert 0 == proc.returncode
		assert str.encode(f"     GITHUB_REGISTRY: some.custom.registry.com\n            SSH_USER: bbaggins\n           REPO_ROOT: {repo_root}\n         CLEAN_AFTER: 7\n DEFAULT_CLONE_PROTO: https\n        DO_NOT_CLEAN: joshmeranda/mytools,joshmeranda/fan\n") == proc.stdout


class TestRepoManagerClone:
	def test_with_no_args(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clone"],
			env={
				_ENV_REPO_ROOT: tmp_path,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 != proc.returncode
		assert b"expected args but found none\n" == proc.stdout

	def test_with_too_many_args(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clone", "a", "b", "c"],
			env={
				_ENV_REPO_ROOT: tmp_path,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 != proc.returncode
		assert b"found more args than expected\n" == proc.stdout

	def test_with_owner_repo_default(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clone", "joshmeranda", "mytools"],
			env={
				_ENV_REPO_ROOT: tmp_path,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		_assert_repo(tmp_path / "joshmeranda" / "mytools", expected_remotes={"origin": "git@github.com:joshmeranda/mytools.git"})

	def test_with_owner_repo_env_ssh(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clone", "joshmeranda", "mytools"],
			env={
				_ENV_REPO_ROOT: tmp_path,
				_ENV_DEFAULT_CLONE_PROTO: "ssh",
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		_assert_repo(tmp_path / "joshmeranda" / "mytools", expected_remotes={"origin": "git@github.com:joshmeranda/mytools.git"})

	def test_with_owner_repo_env_bad(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clone", "joshmeranda", "mytools"],
			env={
				_ENV_REPO_ROOT: tmp_path,
				_ENV_DEFAULT_CLONE_PROTO: "bad",
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 != proc.returncode
		assert b"unsupported DEFAULT_CLONE_PROTO 'bad'\n" == proc.stdout
		assert not (tmp_path / "joshmeranda" / "mytools").exists()

	def test_with_owner_repo_flag_ssh(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clone", "--ssh", "joshmeranda", "mytools"],
			env={
				_ENV_REPO_ROOT: tmp_path,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		_assert_repo(tmp_path / "joshmeranda" / "mytools", expected_remotes={"origin": "git@github.com:joshmeranda/mytools.git"})
	
	def test_with_owner_repo_flag_https(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clone", "--https", "joshmeranda", "mytools"],
			env={
				_ENV_REPO_ROOT: tmp_path,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		_assert_repo(tmp_path / "joshmeranda" / "mytools", expected_remotes={"origin": "https://github.com/joshmeranda/mytools.git"})
	
	def test_with_url_ssh(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clone", "git@github.com:joshmeranda/mytools.git"],
			env={
				_ENV_REPO_ROOT: tmp_path,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		_assert_repo(tmp_path / "joshmeranda" / "mytools", expected_remotes={"origin": "git@github.com:joshmeranda/mytools.git"})

	def test_with_url_https(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clone", "https://github.com/joshmeranda/mytools.git"],
			env={
				_ENV_REPO_ROOT: tmp_path,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		_assert_repo(tmp_path / "joshmeranda" / "mytools", expected_remotes={"origin": "https://github.com/joshmeranda/mytools.git"})

	def test_with_bad_scheme(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clone", "https://gitub.com/joshmeranda/mytools"],
			env={
				_ENV_REPO_ROOT: tmp_path,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 != proc.returncode
		assert b"could not detect owner and repo from url\n" == proc.stdout
		assert not (tmp_path / "joshmeranda" / "mytools").exists()


def _clone_repos(tmp_path_factory: pytest.TempPathFactory) -> list[pathlib.Path]:
	'''_repo_root creates a new temporary directory and populates it with repositories. The returns list contains the REPO_ROOT followe by the cloned repos.'''
	repo_root = tmp_path_factory.mktemp("repos")

	joshmeranda_mytools = repo_root / "joshmeranda" / "mytools"
	joshmeranda_wrash = repo_root / "joshmeranda" / "wrash"
	joshmeranda_fan = repo_root / "joshmeranda" / "fan"

	# note: since we are not cloning static repos, the run time for this func will likely increase over time
	_ = git.Repo.clone_from(url="https://github.com/joshmeranda/mytools.git", to_path=joshmeranda_mytools)
	_ = git.Repo.clone_from(url="https://github.com/joshmeranda/wrash.git", to_path=joshmeranda_wrash)
	_ = git.Repo.clone_from(url="https://github.com/joshmeranda/fan.git", to_path=joshmeranda_fan)

	return [repo_root, joshmeranda_mytools, joshmeranda_wrash, joshmeranda_fan]


@pytest.fixture(scope="function")
def _repo_root(tmp_path_factory: pytest.TempPathFactory) -> list[pathlib.Path]:
	return _clone_repos(tmp_path_factory)


def _make_path_old(path: pathlib.Path, days_old: int):
	dir_stack = [path]
	new_time = (datetime.datetime.now() - datetime.timedelta(days=days_old)).timestamp()

	os.utime(path, times=(new_time, new_time))

	while len(dir_stack) > 0:
		for child in dir_stack.pop().iterdir():
			if child.is_dir():
				dir_stack.append(child)
			
			os.utime(child, times=(new_time, new_time))


@pytest.fixture(scope="function")
def _repo_root_old(_repo_root: list[pathlib.Path]) -> list[pathlib.Path]:
	_make_path_old(_repo_root[2], 10)
	_make_path_old(_repo_root[3], 30)

	return _repo_root


class TestRepoManagerClean:
	def test_with_non_existent_root(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clean"],
			env={
				_ENV_REPO_ROOT: tmp_path / "repos",
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert b"" == proc.stdout

	def test_with_empty_root(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clean"],
			env={
				_ENV_REPO_ROOT: tmp_path,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert b"" == proc.stdout

	def test_with_up_to_date_root(self, _repo_root: list[pathlib.Path]):
		repo_root = _repo_root[0]

		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clean"],
			env={
				_ENV_REPO_ROOT: repo_root,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert b"" == proc.stdout

	def test_with_old_root_yes_to_all(self, _repo_root_old: list[pathlib.Path]):
		repo_root = _repo_root_old[0]

		proc = subprocess.run(
			input=b'\n'.join([b"y", b"y"]),
			args=[_REPO_MANAGER_PATH, "clean"],
			env={
				_ENV_REPO_ROOT: repo_root,
				_ENV_CLEAN_AFTER: "7"
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert b"delete 'joshmeranda/fan'? [N|y]\ndelete 'joshmeranda/wrash'? [N|y]\n" == proc.stdout

		assert _repo_root_old[1].exists()
		assert not _repo_root_old[2].exists()
		assert not _repo_root_old[3].exists()
	
	def test_with_old_root_no_to_some(self, _repo_root_old: list[pathlib.Path]):
		repo_root = _repo_root_old[0]

		proc = subprocess.run(
			input=b"\n".join([b"n", b"y"]),
			args=[_REPO_MANAGER_PATH, "clean"],
			env={
				_ENV_REPO_ROOT: repo_root,
				_ENV_CLEAN_AFTER: "7"
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert b"delete 'joshmeranda/fan'? [N|y]\ndelete 'joshmeranda/wrash'? [N|y]\n" == proc.stdout

		assert _repo_root_old[1].exists()
		assert not _repo_root_old[2].exists()
		assert _repo_root_old[3].exists()

	def test_with_old_root_force(self, _repo_root_old: list[pathlib.Path]):
		repo_root = _repo_root_old[0]

		proc = subprocess.run(
			input=b"ny",
			args=[_REPO_MANAGER_PATH, "clean", "--yes"],
			env={
				_ENV_REPO_ROOT: repo_root,
				_ENV_CLEAN_AFTER: "7"
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert b"" == proc.stdout

		assert _repo_root_old[1].exists()
		assert not _repo_root_old[2].exists()
		assert not _repo_root_old[3].exists()
	
	def test_with_old_root_after_flag(self, _repo_root_old: list[pathlib.Path]):
		repo_root = _repo_root_old[0]

		proc = subprocess.run(
			input=b"\n".join([b"y", b"y"]),
			args=[_REPO_MANAGER_PATH, "clean", "--after", "7"],
			env={
				_ENV_REPO_ROOT: repo_root,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert b"delete 'joshmeranda/fan'? [N|y]\ndelete 'joshmeranda/wrash'? [N|y]\n" == proc.stdout

		assert _repo_root_old[1].exists()
		assert not _repo_root_old[2].exists()
		assert not _repo_root_old[3].exists()

	def test_with_old_root_with_invalid_answer(self, _repo_root_old: list[pathlib.Path]):
		repo_root = _repo_root_old[0]

		proc = subprocess.run(
			input=b'\n'.join([b"yeppers", b"y"]),
			args=[_REPO_MANAGER_PATH, "clean"],
			env={
				_ENV_REPO_ROOT: repo_root,
			},
			capture_output=True,	
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert b"delete 'joshmeranda/fan'? [N|y]\ndelete 'joshmeranda/fan'? [N|y]\n" == proc.stdout

		assert _repo_root_old[1].exists()
		assert _repo_root_old[2].exists()
		assert not _repo_root_old[3].exists()

	def test_with_old_root_with_default_answer(self, _repo_root_old: list[pathlib.Path]):
		repo_root = _repo_root_old[0]

		proc = subprocess.run(
			input=b'\n'.join([b"", b"y"]),
			args=[_REPO_MANAGER_PATH, "clean"],
			env={
				_ENV_REPO_ROOT: repo_root,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert b"delete 'joshmeranda/fan'? [N|y]" == proc.stdout

		assert _repo_root_old[1].exists()
		assert _repo_root_old[2].exists()
		assert _repo_root_old[3].exists()

	def test_with_ucommited_changes(self, _repo_root_old: list[pathlib.Path]):
		new_file = (_repo_root_old[3] / "new_file")
		new_file.write_text("abc")
		new_time = (datetime.datetime.now() - datetime.timedelta(days=30)).timestamp()
		os.utime(new_file, times=(new_time, new_time))
		os.utime(_repo_root_old[3], times=(new_time, new_time))

		repo_root = _repo_root_old[0]

		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clean"],
			env={
				_ENV_REPO_ROOT: repo_root,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert b"repo 'joshmeranda/fan' has an unclean worktree, skipping\n" == proc.stdout

		assert _repo_root_old[1].exists()
		assert _repo_root_old[2].exists()
		assert _repo_root_old[3].exists()

	def test_with_do_not_clean(self, _repo_root_old: list[pathlib.Path]):
		repo_root = _repo_root_old[0]

		proc = subprocess.run(
			input=b'\n'.join([b"y"]),
			args=[_REPO_MANAGER_PATH, "clean"],
			env={
				_ENV_REPO_ROOT: repo_root,
				_ENV_CLEAN_AFTER: "7",
				_ENV_DO_NOT_CLEAN: "joshmeranda/repo1,joshmeranda/wrash,joshmeranda/repo2"
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert proc.stdout == b"delete 'joshmeranda/fan'? [N|y]\nskipping joshmeranda/wrash\n"

		assert _repo_root_old[1].exists()
		assert _repo_root_old[2].exists()
		assert not _repo_root_old[3].exists()

	def test_with_no_remotes(self, _repo_root_old: list[pathlib.Path]):
		repo_root = _repo_root_old[0]

		fan_repo = git.Repo(_repo_root_old[3])
		fan_repo.delete_remote(fan_repo.remote("origin"))

		proc = subprocess.run(
			args=[_REPO_MANAGER_PATH, "clean"],
			env={
				_ENV_REPO_ROOT: repo_root,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert b"repo 'joshmeranda/fan' has no remotes, skipping\n" == proc.stdout

		assert _repo_root_old[1].exists()
		assert _repo_root_old[2].exists()
		assert _repo_root_old[3].exists()


@pytest.fixture(scope="class")
def _repo_root_list(tmp_path_factory: pytest.TempPathFactory) -> list[pathlib.Path]:

	repos = _clone_repos(tmp_path_factory)

	mytools_repo = git.Repo(repos[1])
	mytools_repo.delete_remote(mytools_repo.remote("origin"))

	wrash_repo = git.Repo(repos[2])

	fan_repo = git.Repo(repos[3])
	fan_repo.create_remote("upstream", fan_repo.remote("origin").url)

	return repos


class TestRepoManagerList:
	def test_list(self, _repo_root_list: list[pathlib.Path]):
		repo_root = _repo_root_list[0]

		proc = subprocess.run(
			input=b'\n'.join([b"y"]),
			args=[_REPO_MANAGER_PATH, "list"],
			env={
				_ENV_REPO_ROOT: repo_root,
			},
			capture_output=True,
			timeout=_REPO_MANAGER_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert b"\n".join([
			b"owner/repo                         origin                                            upstream                                          ",
			b"joshmeranda/fan                    https://github.com/joshmeranda/fan.git            https://github.com/joshmeranda/fan.git            ",
			b"joshmeranda/mytools                                                                                                                    ",
			b"joshmeranda/wrash                  https://github.com/joshmeranda/wrash.git                                                            \n",
		]) == proc.stdout