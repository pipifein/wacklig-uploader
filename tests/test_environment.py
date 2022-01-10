import os
from unittest import mock
from unittest.mock import Mock

from wacklig import get_ci_info, github_action_env, jenkins_env, search_env


@mock.patch.dict(os.environ, {"CI_FOOBAR": "bazqux"})
def test_search_env_found():
    value = search_env("CI_FOOBAR")
    assert value == "bazqux"


def test_search_env_notfound():
    value = search_env("CI_FOOBAR")
    assert value is None


@mock.patch.dict(os.environ, {"JENKINS_URL": "https://jenkins.example.org/job/3f786850e3"})
@mock.patch.dict(os.environ, {"ghprbSourceBranch": "testdrive"})
@mock.patch.dict(os.environ, {"GIT_COMMIT": "3f786850e387550fdab836ed7e6dc881de23001b"})
@mock.patch.dict(os.environ, {"ghprbPullId": "111"})
@mock.patch.dict(os.environ, {"BUILD_NUMBER": "42"})
def test_get_ci_info_jenkins():
    data = get_ci_info()
    assert data == {
        "service": "jenkins",
        "branch": "testdrive",
        "commit": "3f786850e387550fdab836ed7e6dc881de23001b",
        "pr": "111",
        "build": "42",
    }


@mock.patch.dict(os.environ, {"GITHUB_ACTION": "true"})
@mock.patch.dict(os.environ, {"GITHUB_SHA": "3f786850e387550fdab836ed7e6dc881de23001b"})
@mock.patch.dict(os.environ, {"GITHUB_REF": "refs/pull/111/merge"})
@mock.patch.dict(os.environ, {"GITHUB_HEAD_REF": "feature-branch-1"})
@mock.patch.dict(os.environ, {"GITHUB_RUN_ID": "42"})
def test_get_ci_info_github_with_pr():
    data = get_ci_info()
    assert data == {
        "service": "github-actions",
        "commit": "3f786850e387550fdab836ed7e6dc881de23001b",
        "build": "42",
        "branch": "feature-branch-1",
        "pr": "111",
    }


@mock.patch.dict(os.environ, {"GITHUB_ACTION": "true"})
@mock.patch.dict(os.environ, {"GITHUB_SHA": "3f786850e387550fdab836ed7e6dc881de23001b"})
@mock.patch.dict(os.environ, {"GITHUB_REF": "refs/heads/feature-branch-1"})
@mock.patch.dict(os.environ, {"GITHUB_HEAD_REF": ""})
@mock.patch.dict(os.environ, {"GITHUB_RUN_ID": "42"})
def test_get_ci_info_github_with_branch():
    data = get_ci_info()
    assert data == {
        "service": "github-actions",
        "commit": "3f786850e387550fdab836ed7e6dc881de23001b",
        "build": "42",
        "branch": "feature-branch-1",
    }


@mock.patch.dict(os.environ, {"JENKINS_URL": ""})
@mock.patch.dict(os.environ, {"GITHUB_ACTION": ""})
@mock.patch(
    "wacklig.check_output",
    Mock(side_effect=["testdrive", "3f786850e387550fdab836ed7e6dc881de23001b"]),
)
def test_get_ci_info_local():
    data = get_ci_info()
    assert data == {
        "service": "local",
        "branch": "testdrive",
        "commit": "3f786850e387550fdab836ed7e6dc881de23001b",
    }
