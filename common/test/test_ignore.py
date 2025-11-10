import subprocess
import os
import pathlib
import pytest
import datetime
import git

_IGNORE_TIMEOUT: int = 30
_IGNORE_PATH: str = os.path.abspath("common/ignore.sh")

_ENV_GITIGNORE_REPO_ROOT = "GITIGNORE_REPO_ROOT"
_ENV_GITIGNORE_PATH = "GITIGNORE_PATH"


def _setup_repo(path: str, back_n_commits: int=0):
	_ = git.Repo.clone_from(url="https://github.com/github/gitignore.git", to_path=path)

	if back_n_commits > 0:
		# todo: figure out how to do this with GitPython
		proc = subprocess.run(
			args=["git", "reset", "--hard", "HEAD" + "^"*back_n_commits],
			cwd=os.path.join(path),
			capture_output=True,
		)

		if proc.returncode != 0:
			pytest.fail("repo setup failed")


@pytest.fixture(scope="class")
def _gitignore_repo_root(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
	repo_root = tmp_path_factory.mktemp("gitignore_repo")
	_setup_repo(str(repo_root / "gitignore"))
	return repo_root


class TestIgnoreTarget:
	def test_no_target(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_IGNORE_PATH, "target"],
			env={
				_ENV_GITIGNORE_REPO_ROOT: str(tmp_path),
			},
			capture_output=True,
			timeout=_IGNORE_TIMEOUT
		)

		assert proc.returncode != 0
		assert proc.stdout == b"expected at least 1 target but found none\n"

	def test_no_repo(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_IGNORE_PATH, "target", "go"],
			env={
				_ENV_GITIGNORE_REPO_ROOT: str(tmp_path),
			},
			capture_output=True,
			timeout=_IGNORE_TIMEOUT
		)

		assert proc.returncode != 0
		assert proc.stdout == b"no gitignores found at '" + bytes(tmp_path.joinpath("gitignore")) + b"'\n"

	def test_one_target(self, _gitignore_repo_root: pathlib.Path, tmp_path: pathlib.Path):
		ignore_path = tmp_path / ".gitignore"

		proc = subprocess.run(
			args=[_IGNORE_PATH, "target", "go"],
			env={
				_ENV_GITIGNORE_REPO_ROOT: str(_gitignore_repo_root),
				_ENV_GITIGNORE_PATH: str(ignore_path),
			},
			capture_output=True,
			timeout=_IGNORE_TIMEOUT
		)

		assert proc.returncode == 0
		assert ignore_path.exists()

		expected_gitignore='''# # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This gitignore was auto-generated using the standard templates published by  #
# github here: github.com/github/gitignore                                     #
# # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # # # # # # #

## Go.gitignore
'''		

		expected_gitignore += (_gitignore_repo_root / "gitignore" / "Go.gitignore").read_text()

		with open(ignore_path) as f:
			assert f.read() == expected_gitignore

	def test_multiple_targets(self, _gitignore_repo_root: pathlib.Path, tmp_path: pathlib.Path):
		ignore_path = tmp_path / ".gitignore"

		proc = subprocess.run(
			args=[_IGNORE_PATH, "target", "go", "python"],
			env={
				_ENV_GITIGNORE_REPO_ROOT: str(_gitignore_repo_root),
				_ENV_GITIGNORE_PATH: str(ignore_path),
			},
			capture_output=True,
			timeout=_IGNORE_TIMEOUT
		)

		assert proc.returncode == 0
		assert ignore_path.exists()

		expected_gitignore='''# # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# This gitignore was auto-generated using the standard templates published by  #
# github here: github.com/github/gitignore                                     #
# # # # # # # # # # # ## # # # # # # # # # # # # # # # # # # # # # # # # # # # #

## Go.gitignore
'''		

		expected_gitignore += (_gitignore_repo_root / "gitignore" / "Go.gitignore").read_text()
		expected_gitignore += "\n" + "## Python.gitignore\n" + (_gitignore_repo_root / "gitignore" / "Python.gitignore").read_text()

		with open(ignore_path) as f:
			assert f.read() == expected_gitignore

	def test_no_exist(self, _gitignore_repo_root: pathlib.Path, tmp_path: pathlib.Path):
		ignore_path = tmp_path / ".gitignore"

		proc = subprocess.run(
			args=[_IGNORE_PATH, "target", "no-exist"],
			env={
				_ENV_GITIGNORE_REPO_ROOT: str(_gitignore_repo_root),
				_ENV_GITIGNORE_PATH: str(ignore_path),
			},
			capture_output=True,
			timeout=_IGNORE_TIMEOUT
		)

		assert proc.returncode != 0
		assert proc.stdout == b"no gitignore for target 'no-exist'\n"
		assert not ignore_path.exists()

	def test_mix_exist_no_exist(self, _gitignore_repo_root: pathlib.Path, tmp_path: pathlib.Path):
		ignore_path = tmp_path / ".gitignore"

		proc = subprocess.run(
			args=[_IGNORE_PATH, "target", "go", "no-exist"],
			env={
				_ENV_GITIGNORE_REPO_ROOT: str(_gitignore_repo_root),
				_ENV_GITIGNORE_PATH: str(ignore_path),
			},
			capture_output=True,
			timeout=_IGNORE_TIMEOUT
		)

		assert proc.returncode != 0
		assert proc.stdout == b"no gitignore for target 'no-exist'\n"
		assert not ignore_path.exists()

	def test_existing_file(self, _gitignore_repo_root: pathlib.Path, tmp_path: pathlib.Path):
		ignore_path = tmp_path / ".gitignore"
		ignore_path.write_text("# empty .gitignore")

		proc = subprocess.run(
			args=[_IGNORE_PATH, "target", "go"],
			env={
				_ENV_GITIGNORE_REPO_ROOT: str(_gitignore_repo_root),
				_ENV_GITIGNORE_PATH: str(ignore_path),
			},
			capture_output=True,
			timeout=_IGNORE_TIMEOUT
		)

		assert proc.returncode != 0
		assert proc.stdout == b"".join([b"cannot create gitignore '", bytes(ignore_path), b"', file exists\n"])
		assert ignore_path.read_bytes() == b"# empty .gitignore"


def _has_newer_than(path: pathlib.Path, old: float) -> bool:
	for i in path.iterdir():
		if i.stat().st_mtime > old:
			return True

		if i.is_dir():
			return _has_newer_than(i, old)

	return False


class TestIgnoreUpdate:
	def test_no_existing_repo(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_IGNORE_PATH, "update"],
			env={
				_ENV_GITIGNORE_REPO_ROOT: str(tmp_path),
			},
			capture_output=True,
			timeout=_IGNORE_TIMEOUT)
		
		assert proc.returncode == 0
		assert proc.stdout == b"no ignore repository found, cloning from 'https://github.com/github/gitignore'\n"
		assert (tmp_path / "gitignore").exists()

	def test_existing_repo(self, tmp_path: pathlib.Path):
		repo_path = tmp_path / "gitignore"
		_setup_repo(repo_path, back_n_commits=5)

		now = datetime.datetime.now().timestamp()

		proc = subprocess.run(
			args=[_IGNORE_PATH, "update"],
			env={
				_ENV_GITIGNORE_REPO_ROOT: str(tmp_path),
			},
			capture_output=True,
			timeout=_IGNORE_TIMEOUT,
		)

		assert proc.returncode == 0
		assert repo_path.exists()
		# assert _has_newer_than(repo_path, now)
		assert _has_newer_than(tmp_path / "gitignore", now)

	def test_existing_repo_up_to_date(self, tmp_path: pathlib.Path):
		repo_path = tmp_path / "gitignore"
		_setup_repo(repo_path)


		now = datetime.datetime.now().timestamp()

		proc = subprocess.run(
			args=[_IGNORE_PATH, "update"],
			env={
				_ENV_GITIGNORE_REPO_ROOT: str(tmp_path),
			},
			capture_output=True,
			timeout=_IGNORE_TIMEOUT,
		)

		assert proc.returncode == 0
		assert (tmp_path / "gitignore").exists()
		assert not _has_newer_than(repo_path, now)
