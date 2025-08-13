import pathlib


def test_each_common_script_has_test():
	common = pathlib.Path("common")
	common_test = common / "test"

	for child in pathlib.Path("common").iterdir():
		if child.is_file():
			assert (common_test / f"test_{child.stem.replace("-", "_")}.py").exists()