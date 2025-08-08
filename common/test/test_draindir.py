import pathlib
import pytest
import os
import subprocess


_DRAINDIR_TIMEOUT: int = 30
_DRAINDIR_PATH: str = os.path.abspath("common/draindir.sh")


def _assert_files_in(dir: pathlib.Path):
	assert (dir / "file").exists()
	assert (dir / "file").read_text() == "abc"

	assert (dir / ".hidden").exists()
	assert (dir / ".hidden").read_text() == "abc"

	assert (dir / "dir").exists()

	assert (dir / "dir" / "file").exists()
	assert (dir / "dir" / "file").read_text() == "abc"


def _assert_drain(src: pathlib.Path, dst: pathlib.Path):
	assert not src.exists()
	_assert_files_in(dst)


@pytest.fixture(scope="function")
def _drain_src(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
	src = tmp_path_factory.mktemp("src")

	(src / "file").write_text("abc")
	(src / ".hidden").write_text("abc")
	(src / "dir").mkdir()
	(src / "dir" / "file").write_text("abc")

	return src


class TestDraindir:
	def test_non_existant_dir(self, tmp_path: pathlib.Path):
		proc = subprocess.run(
			args=[_DRAINDIR_PATH, tmp_path / "non-existant", tmp_path],
			capture_output=True,
			timeout=_DRAINDIR_TIMEOUT,
		)

		assert 0 != proc.returncode

	def test_empty_dir(self, tmp_path: pathlib.Path):
		src = (tmp_path / "dir")
		src.mkdir()

		proc = subprocess.run(
			args=[_DRAINDIR_PATH, src, tmp_path],
			capture_output=True,
			timeout=_DRAINDIR_TIMEOUT,
		)

		assert 0 == proc.returncode

		assert not src.exists()

	def test_into_cwd(self, tmp_path: pathlib.Path, _drain_src: pathlib.Path):
		proc = subprocess.run(
			args=[_DRAINDIR_PATH, _drain_src, "."],
			cwd=tmp_path,
			capture_output=True,
			timeout=_DRAINDIR_TIMEOUT,
		)

		assert 0 == proc.returncode
		_assert_drain(_drain_src, tmp_path)

	def test_into_dir(self, tmp_path: pathlib.Path, _drain_src: pathlib.Path):
		proc = subprocess.run(
			args=[_DRAINDIR_PATH, _drain_src, tmp_path],
			capture_output=True,
			timeout=_DRAINDIR_TIMEOUT,
		)

		assert 0 == proc.returncode
		_assert_drain(_drain_src, tmp_path)

	def test_into_self(self, _drain_src: pathlib.Path):
		proc = subprocess.run(
			args=[_DRAINDIR_PATH, _drain_src, _drain_src],
			capture_output=True,
			timeout=_DRAINDIR_TIMEOUT,
		)

		assert 0 != proc.returncode
		_assert_files_in(_drain_src)

	def test_too_many_args(self, tmp_path: pathlib.Path,_drain_src: pathlib.Path):
		proc = subprocess.run(
			args=[_DRAINDIR_PATH, tmp_path / "a", tmp_path / "b", _drain_src],
			capture_output=True,
			timeout=_DRAINDIR_TIMEOUT,
		)

		assert 0 != proc.returncode
		assert b"found too many args\n" == proc.stdout

		_assert_files_in(_drain_src)

	def test_missing_dst(self, _drain_src: pathlib.Path):
		proc = subprocess.run(
			args=[_DRAINDIR_PATH, _drain_src],
			capture_output=True,
			timeout=_DRAINDIR_TIMEOUT,
		)

		assert 0 != proc.returncode
		assert b"missing DST arg\n" == proc.stdout

		_assert_files_in(_drain_src)

	def test_missing_dst(self, _drain_src: pathlib.Path):
		proc = subprocess.run(
			args=[_DRAINDIR_PATH],
			capture_output=True,
			timeout=_DRAINDIR_TIMEOUT,
		)

		assert 0 != proc.returncode
		assert b"missing SRC and DST args\n" == proc.stdout

		_assert_files_in(_drain_src)

	def test_with_conflicts(self, tmp_path: pathlib.Path, _drain_src: pathlib.Path):
		(tmp_path / "dir").mkdir()
		(tmp_path / "dir" / "file").write_text("def")

		proc = subprocess.run(
			args=[_DRAINDIR_PATH, _drain_src, tmp_path],
			capture_output=True,
			timeout=_DRAINDIR_TIMEOUT,
		)

		assert 1 == proc.returncode
		assert b"SRC and DST have a conflict 'dir'\n" == proc.stdout

		assert not (tmp_path / "file").exists()
		assert not (tmp_path / ".hidden").exists()
		assert (tmp_path / "dir").exists()
		assert (tmp_path / "dir" / "file").exists()
		assert "def" == (tmp_path / "dir" / "file").read_text()

		_assert_files_in(_drain_src)