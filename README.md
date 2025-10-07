# MyTools

A collection of tools and things. Use if you like!

## Dependencies

For most of these tools I try to stick to pure bash and coreutils, but sometimes that just is not possible or practical. Below are the tools that will let you run all tools:

| Name | Version | Links |
| ---- | ------- | ----- |
| git  | 2.34.1  | https://github.com/rancher/rancher-docs/pull/1852 |
| jq   | 1.6     | https://github.com/jqlang/jq?tab=readme-ov-file#installation |

Versions are what I have used during developed. Other versions may works as well, but have not been tested.

## Testing

All scripts under `common/` must have a test file associate or the tests will fail. if a script is particularly small *and* hard to test, the script can be excluded by updating `common/test/test_common.py`.

To run tests make sure you have created and activated the python virtualenv with:

```
make .venv

# make sure you choose the right activation script for your shell
. .venv/bin/activate
```

From there you can run your tests:

```
# you can find more information on runnning pytest for specific tests or test
# suites on the pytest documentation: https://docs.pytest.org/en/7.1.x/how-to/usage.html
pytest .
```