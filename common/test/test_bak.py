import pathlib
import subprocess
import os


_BAK_TIMEOUT: int = 30
_BAK_PATH: str = os.path.abspath("common/bak.sh")


class TestBak:
	def test_in_same_dir(self, tmp_path: pathlib.Path):
		file = tmp_path / "file"
		file.write_text("abc")

		proc = subprocess.run(
			args=[_BAK_PATH, file],
			cwd=tmp_path,
			capture_output=True,
			timeout=_BAK_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert file.exists()
		assert (tmp_path / "~file").exists()
		assert "abc" == (tmp_path / "~file").read_text()

	def test_different_dirs(self, tmp_path: pathlib.Path):
		file = tmp_path / "file"
		file.write_text("abc")

		proc = subprocess.run(
			args=[_BAK_PATH, file],
			capture_output=True,
			timeout=_BAK_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert file.exists()
		assert (tmp_path / "~file").exists()
		assert "abc" == (tmp_path / "~file").read_text()

	def test_prefix(self, tmp_path: pathlib.Path):
		file = tmp_path / "file"
		file.write_text("abc")

		proc = subprocess.run(
			args=[_BAK_PATH, "--prefix", "prefix-", file],
			cwd=tmp_path,
			capture_output=True,
			timeout=_BAK_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert file.exists()
		assert (tmp_path / "prefix-file").exists()
		assert "abc" == (tmp_path / "prefix-file").read_text()

	def test_suffix(self, tmp_path: pathlib.Path):
		file = tmp_path / "file"
		file.write_text("abc")

		proc = subprocess.run(
			args=[_BAK_PATH, "--suffix", "-suffix", file],
			cwd=tmp_path,
			capture_output=True,
			timeout=_BAK_TIMEOUT,
		)

		assert 0 == proc.returncode
		assert file.exists()
		assert (tmp_path / "file-suffix").exists()
		assert "abc" == (tmp_path / "file-suffix").read_text()

	def test_multiple_files(self, tmp_path: pathlib.Path):
		file_a = tmp_path / "file_a"
		file_a.write_text("abc")

		file_b = tmp_path / "file_b"
		file_b.write_text("abc")

		proc = subprocess.run(
			args=[_BAK_PATH, file_a, file_b],
			cwd=tmp_path,
			capture_output=True,
			timeout=_BAK_TIMEOUT,
		)

		assert 0 == proc.returncode

		assert file_a.exists()
		assert (tmp_path / "~file_a").exists()
		assert "abc" == (tmp_path / "~file_a").read_text()

		assert file_b.exists()
		assert (tmp_path / "~file_b").exists()
		assert "abc" == (tmp_path / "~file_b").read_text()

	def test_missing_prefix_value(self):
		proc = subprocess.run(
			args=[_BAK_PATH, "--prefix"],
			capture_output=True,
			timeout=_BAK_TIMEOUT,
		)

		assert 0 != proc.returncode
		assert b"expected prefix but found none\n" == proc.stdout

	def test_missing_suffix_value(self):
		proc = subprocess.run(
			args=[_BAK_PATH, "--suffix"],
			capture_output=True,
			timeout=_BAK_TIMEOUT,
		)

		assert 0 != proc.returncode
		assert b"expected suffix but found none\n" == proc.stdout

	def test_missing_file(self):
		proc = subprocess.run(
			args=[_BAK_PATH],
			capture_output=True,
			timeout=_BAK_TIMEOUT,
		)

		assert 0 != proc.returncode
		assert b"expected files but found none\n" == proc.stdout