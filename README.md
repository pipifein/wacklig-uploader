# wacklig-uploader

## About

A Python script to upload test results to [wacklig].


## Tests

```shell
python3 -m venv .venv
source .venv/bin/activate
pip install --requirement=requirements-test.txt

# Run all tests.
pytest

# Run specific tests.
pytest -k test_upload_files
```

[wacklig]: https://wacklig.pipifein.dev/
