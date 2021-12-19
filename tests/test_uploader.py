import io
import os
import re
import tempfile
from pathlib import Path
from unittest import mock
from unittest.mock import Mock

import pytest
from mocket import Mocket, MocketEntry, Mocketizer

import wacklig
from tests.conftest import here
from wacklig import find_test_files, upload_files


def test_find_test_files(fs):
    fs.create_file(file_path=Path("test-results/test/report1.xml"))
    fs.create_file(file_path=Path("test-results/test/nested/report2.xml"))
    fs.create_file(file_path=Path("test-results/test/nested/more/report3.xml"))
    assert find_test_files() == [
        str(Path("test-results/test/report1.xml")),
        str(Path("test-results/test/nested/report2.xml")),
        str(Path("test-results/test/nested/more/report3.xml")),
    ]


def test_upload_files_empty():
    with pytest.raises(SystemExit) as ex:
        upload_files(token=None, server=None, ci_info=None, files=None)
    assert ex.match(re.escape("No test files found"))


NamedTemporaryFile = tempfile.NamedTemporaryFile


def tempfile_factory():
    return NamedTemporaryFile(delete=False)


# Augment `NamedTemporaryFile` to not being deleted. We need it for verifying.
@mock.patch.object(wacklig.tempfile, "NamedTemporaryFile", tempfile_factory)
def test_upload_files_success_synthetic(capsys):

    # Prepare fixture data.
    wacklig_server = "https://wacklig.example.org"
    wacklig_token = "WACKLIG_TOKEN"
    ci_info = {
        "service": "local",
        "branch": "testdrive",
        "commit": "3f786850e387550fdab836ed7e6dc881de23001b",
    }
    test_report_files = [os.path.join(here, "tests/junit-example.xml")]

    # Invoke `upload_files` with mocked `urllib.urlopen()`.
    # TODO: Use a more realistic response payload here. Probably JSON?
    urlopen_mock = Mock(return_value=io.BytesIO(b"HTTP response body from wacklig service"))
    with mock.patch.object(wacklig, "urlopen", urlopen_mock):
        upload_files(
            token=wacklig_token,
            server=wacklig_server,
            ci_info=ci_info,
            files=test_report_files,
        )

    # Proof that the request URL has correct information.
    urlopen_mock.assert_called_once_with(
        "https://wacklig.example.org/api/v1/upload?service=local&branch=testdrive&commit=3f786850e387550fdab836ed7e6dc881de23001b&token=WACKLIG_TOKEN",
        data=mock.ANY,
    )

    # Proof that the HTTP request body content is a gzip payload.
    filepath = urlopen_mock.call_args[1]["data"].name
    assert open(filepath, "rb").read().startswith(b"\x1f\x8b\x08")

    # TODO: Proof that it is actually a .tar.gz payload, having the correct content.

    # Proof that the HTTP response body has been printed to stdout.
    stdout = capsys.readouterr().out.strip()
    assert stdout == "HTTP response body from wacklig service"

    # Gracefully clean up temporary files.
    try:
        os.unlink(filepath)
    except:  # pragma:nocover
        pass


def test_upload_files_success_real(capsys):

    # Prepare fixture data.
    wacklig_server = "https://wacklig.example.org"
    wacklig_token = "WACKLIG_TOKEN"
    ci_info = {
        "service": "local",
        "branch": "testdrive",
        "commit": "3f786850e387550fdab836ed7e6dc881de23001b",
    }
    test_report_files = [os.path.join(here, "tests/junit-example.xml")]

    # Invoke `upload_files` with mocked `socket` library.
    with Mocketizer():
        addr = ("wacklig.example.org", 443)
        # TODO: Use a more realistic response payload here. Probably JSON?
        Mocket.register(
            MocketEntry(location=addr, responses=["HTTP/1.1 200 OK\r\n\r\nHTTP response body from wacklig service"])
        )
        upload_files(
            token=wacklig_token,
            server=wacklig_server,
            ci_info=ci_info,
            files=test_report_files,
        )

    # Proof that the HTTP response body has been printed to stdout.
    stdout = capsys.readouterr().out.strip()
    assert stdout == "HTTP response body from wacklig service"


@mock.patch.dict(os.environ, {"GITHUB_ACTION": "true"})
@mock.patch.dict(os.environ, {"GITHUB_SHA": "3f786850e387550fdab836ed7e6dc881de23001b"})
@mock.patch.dict(os.environ, {"GITHUB_RUN_ID": "42"})
def test_main(mocker, fs, capsys):

    # Prepare fixture data.
    wacklig_server = "https://wacklig.example.org"
    wacklig_token = "WACKLIG_TOKEN"
    report_files = ["test-results/test/report1.xml", "test-results/test/nested/report2.xml"]

    # Create files in fake filesystem.
    list(map(fs.create_file, report_files))

    # Pretend to invoke main program.
    mocker.patch("sys.argv", ["wacklig-upload", "--server", wacklig_server, "--token", wacklig_token])
    mocker.patch.object(wacklig, "find_test_files", Mock(return_value=report_files))
    mocker.patch.object(wacklig, "urlopen", Mock(return_value=io.BytesIO(b"HTTP response body from wacklig service")))
    wacklig.main()

    # Proof that the expected message has been written to stdout.
    stdout = capsys.readouterr().out.strip()
    assert "Uploaded 2 files" in stdout
