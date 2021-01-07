#!/usr/bin/env python3

"""
Find files that look like test result reports and upload them to wacklig.pipifein.dev
"""

import os
import argparse
import tarfile
import tempfile
from urllib.request import urlopen
from urllib.parse import urlencode
from glob import glob


def search_env(*options):
    for option in options:
        value = os.environ.get(option)
        if value:
            return value


def jenkins_env():
    return {
        'service': 'jenkins',
        'branch': search_env('ghprbSourceBranch', 'GIT_BRANCH', 'BRANCH_NAME'),
        'commit': search_env('ghprbActualCommit', 'GIT_COMMIT'),
        'pr': search_env('ghprbPullId', 'CHANGE_ID'),
        'build': os.environ.get('BUILD_NUMBER'),
    }


def get_ci_info():
    if os.environ.get('JENKINS_URL'):
        return jenkins_env()

    return None


def find_test_files():
    return glob('**/build/test-results/test/*.xml', recursive=True)


def upload_files(server, ci_info, files):
    if not files:
        raise SystemExit('No test files found')
    with tempfile.NamedTemporaryFile() as fd:
        with tarfile.open(fd.name, 'w:gz') as tar:
            for filename in files:
                tar.add(filename)
        ci_info = {k: v for (k, v) in ci_info.items() if v}
        params = ci_info and '?' + urlencode(ci_info) or ''
        urlopen(server + '/upload' + params, data=fd)


def main():
    parser = argparse.ArgumentParser('wacklig')
    parser.add_argument('--server', type=str, default='https://wacklig.pipifein.dev')
    args = parser.parse_args()
    print(args)
    ci_info = get_ci_info()
    print(ci_info)
    files = find_test_files()
    upload_files(args.server, ci_info, files)


if __name__ == "__main__":
    main()
